# menuTitle: Smoother Operator Helper

import ezui
import math
from mojo.UI import getDefault


def lerp(factor, v1, v2):
    return v1 + factor * (v2 - v1)
    

def get_surrounding_points(pt):
    '''Returns previous and next points of a give point.'''
    c = pt.contour
    i = pt.index
    prev_pt = c.points[i-1]
    next_pt = c.points[i-len(c.points)+1]
    return prev_pt, next_pt


def check_same_pt_flavor(pt, other_pt):
    '''Checks whether the surrounding point structure of one pt resemble another’s.'''
    prev_pt, next_pt = get_surrounding_points(pt)
    o_prev_pt, o_next_pt = get_surrounding_points(other_pt)
    if o_prev_pt.type == prev_pt.type and o_next_pt.type == next_pt.type:
        return True
    return False


def calc_ratio(pt):
    '''Returns distance ratio (of contiguous points) of a given point.'''
    prev_pt, next_pt = get_surrounding_points(pt)
    p1, p2, p3 = (prev_pt.x, prev_pt.y), (pt.x, pt.y), (next_pt.x, next_pt.y)
    rin  = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
    rout = math.hypot(p3[0] - p2[0], p3[1] - p2[1])
    return rin / rout
    
        
def change_ratio(pt, new_ratio, off_curve_change=.1):
    '''Changes the position of a point, given a desired ratio.'''
    g = pt.glyph
    prev_pt, next_pt = get_surrounding_points(pt)
    p1, p2, p3 = (prev_pt.x, prev_pt.y), (pt.x, pt.y), (next_pt.x, next_pt.y)
    factor = new_ratio / (new_ratio + 1)
    in_factor = -new_ratio  # Based on 2 and 3
    out_factor = (new_ratio + 1) / new_ratio  # Based on 1 and 2
    off_pt_amount = len([pt for pt in [prev_pt, next_pt] if pt.type == "offcurve"])
    off_soften = off_curve_change / off_pt_amount   # Amount each off-curve point move shares the load
    on_soften  = 1 - off_soften * off_pt_amount  # On-curve moves less as a result
    # Figure out the coordinates of the on-curve
    new_pt_coords = (lerp(factor, p1[0], p3[0]), lerp(factor, p1[1], p3[1]))
    new_pt_coords = (lerp(on_soften, p2[0], new_pt_coords[0]), lerp(on_soften, p2[1], new_pt_coords[1]))
    # Figure out the coordinates of the previous pt
    new_ppt_coords = (lerp(in_factor, p2[0], p3[0]), lerp(in_factor, p2[1], p3[1]))
    new_ppt_coords = (lerp(off_soften, p1[0], new_ppt_coords[0]), lerp(off_soften, p1[1], new_ppt_coords[1]))
    # Figure out the coordinates of the next pt
    new_npt_coords = (lerp(out_factor, p1[0], p2[0]), lerp(out_factor, p1[1], p2[1]))
    new_npt_coords = (lerp(off_soften, p3[0], new_npt_coords[0]), lerp(off_soften, p3[1], new_npt_coords[1]))
    # Change 2 or 3 points’ coords
    with g.undo("Change point ratio"):
        change_coords(pt, new_pt_coords)
        if prev_pt.type == "offcurve":
            change_coords(prev_pt, new_ppt_coords)
        if next_pt.type == "offcurve":
            change_coords(next_pt, new_npt_coords)
            
            
def change_coords(pt, coords):
    if getDefault("glyphViewRoundValues") == 1:
        coords = tuple([round(coord) for coord in coords])
    pt.x, pt.y = coords
    

def get_all_corresponding_pts(pt):
    '''
    Returns a set of all point objects in all open 
    fonts that correspond to one given point, based on index.
    '''
    g_name = pt.glyph.name
    c_i = pt.contour.index
    all_pts = {pt}
    for f in AllFonts():
        other_pt = f[g_name].contours[c_i].points[pt.index]
        if other_pt.type == pt.type and check_same_pt_flavor(pt, other_pt):
            all_pts.add(other_pt)
        else:
            print(f"Check point relevance in {f.info.styleName} {g_name}.")
    return all_pts
    
    
def get_average_ratios(pts):
    '''Returns average ratio for given points.'''
    ratios = [calc_ratio(pt) for pt in pts]
    return sum(ratios) / len(ratios)
    
    
def sync_ratios(pt, mode="follow", off_curve_change=.1):
    '''Syncs ratios of all corresponding pts of a point. '''
    pts = get_all_corresponding_pts(pt)
    if mode == "follow":
        desired_ratio = calc_ratio(pt)
    elif mode == "average":
        desired_ratio = get_average_ratios(pts)
    else:
        return
    for pt in pts:
        change_ratio(pt, desired_ratio, off_curve_change=off_curve_change)
        
        

class SmoothSynchronizer(ezui.WindowController):

    def build(self):
        content = """
        Change:
        --X--                   @offCurveChangeSlider
        * HorizontalStack
        > !* Off-Curves         @offCurveLabel
        > !* On-Curves          @onCurveLabel
        
        ---
        
        (X) Match Selection     @modeRadios
        ( ) Average All
        
        (Synchronize)           @syncButton
        (Undo)                  @undoButton
        """
        descriptionData = dict(
            offCurveChangeSlider=dict(
                value=0.15,
                width=180,
                minValue=0,
                maxValue=1,
                sizeStyle="mini",
            ),
            offCurveLabel=dict(
                gravity="trailing",
            ),
            mainForm=dict(
                titleColumnWidth=70,
                itemColumnWidth=120
            ),
            syncButton=dict(
                width='fill'
            ),
            undoButton=dict(
                width='fill'
            ),
        )
        self.w = ezui.EZPanel(
            title="Smooth Synchronizer",
            content=content,
            descriptionData=descriptionData,
            controller=self
        )
        self.clear_saved_states()
        self.w.setDefaultButton(self.w.getItem("syncButton"))
        self.w.getNSWindow().setTitlebarAppearsTransparent_(True)

    def started(self):
        self.w.open()
        
    def destroy(self):
        self.saved_states = []
        
    def clear_saved_states(self):
        self.saved_states = []
        self.w.getItem("undoButton").enable(False)
        
    def save_state(self, ref_pts):
        this_state = {} 
        for p in ref_pts:
            for corr_pt in list(get_all_corresponding_pts(p)):
                for pt in list(get_surrounding_points(corr_pt)) + [corr_pt]:
                    this_state.update({pt: (pt.x, pt.y)})
        self.saved_states.append(this_state)
        self.w.getItem("undoButton").enable(True)
        
    def syncButtonCallback(self, sender):
        mode = ['follow', 'average'][self.w.getItem("modeRadios").get()]
        off_curve_change = self.w.getItem("offCurveChangeSlider").get()
        g = CurrentGlyph()
        self.save_state(g.selectedPoints)
        for pt in g.selectedPoints:
            sync_ratios(pt, mode=mode, off_curve_change=off_curve_change)
        for f in AllFonts():
            if g.name in f.keys():
                f[g.name].changed()
                
    def undoButtonCallback(self, sender):
        glyphs = set()
        for pt, previous_coords in self.saved_states[-1].items():
            pt.x, pt.y = previous_coords
            glyphs.add(pt.glyph)
        for g in glyphs:
            g.changed()
        self.saved_states.pop()
        if not self.saved_states:
            self.clear_saved_states()

SmoothSynchronizer()