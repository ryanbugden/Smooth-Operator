import math
from fontParts.world import OpenFont
from fontTools.pens.recordingPen import RecordingPointPen

'''
Check the angle/ratio of glyphs in fonts. 
Intended to be run after prepolation.

Heavily based on code from the Angle/Ratio tool from Erik van Blokland:
https://github.com/LettError/angleRatioTool

Ryan Bugden
23.04.18 - Simple tool
24.01.23 - Extension
'''


def average_list(lst):
    return round(sum(lst) / len(lst), 2)
    

def calc_angle_gamut(angle_1, angle_2):
    gamut = abs(angle_2 - angle_1)
    if gamut > 180:
        gamut = 360 - gamut
    return round(gamut, 2)
    

def calc_quality_score(angle_gamut, ratio_gamut, angle_tol, ratio_tol):
    '''Calculate the quality score. Returns number from 0 to 100.'''
    if angle_gamut < angle_tol or ratio_gamut < ratio_tol:
        quality_score = 100
    else:
        # quality_score = (-angle_tol * 10 * angle_gamut) + (-ratio_tol * 10 * ratio_gamut) + 100
        angle_quality_score = 100 - (angle_gamut / angle_tol) 
        ratio_quality_score = 100 - (ratio_gamut / ratio_tol)
        quality_score = (angle_quality_score + ratio_quality_score) / 2
    quality_score = max([0, quality_score])
    return quality_score


def calc_vector(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return x2 - x1, y2 - y1


def calc_angle(p1, p2):
    dx, dy = calc_vector(p1, p2)
    return math.atan2(dy, dx)
    
    
def calc_ratio(p1, p2, p3):
    rin  = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
    rout = math.hypot(p3[0] - p2[0], p3[1] - p2[1])
    if rout == 0:
        return rin
    return rin / rout


def collinear(p1, p2, p3, error_in_degrees=3):
    '''Find if three points are collinear. From Frank Griesshammer.'''
    angle_1 = calc_angle(p1, p2)
    angle_2 = calc_angle(p2, p3)

    if abs(angle_2 - angle_1) < math.radians(error_in_degrees):
        return True
    return False

    
def reformat_pen_output(pen_value):
    main_list = []
    new_list = []
    c_i, p_i = 0, 0
    for entry in pen_value:    
        # If the entry is beginPath...
        if entry[0] == "beginPath":
            continue
        # If it's an endPath...
        elif entry[0] == "endPath" or entry[0] == ():
            # ... advance the contour, and append the new list
            main_list.append(new_list)
            new_list = []
            c_i += 1
            p_i = 0
            continue
        new_list.append(((c_i, p_i), entry[1]))
        p_i += 1
    return main_list
    
    
def get_angle_ratio(p, contour_point_info, check_triangles, check_circles, check_non_smooth):
    i = p[0][1]
    c = contour_point_info
    l = len(contour_point_info)
    pppt = c[i-2]
    ppt = c[i-1]
    npt = c[(i+1)%l]
    nnpt = c[(i+2)%l]

    apt = bpt = cpt = r = rin = rout = None
    
    # Try to suss out non-smooth-flag points
    if check_non_smooth == True and p[1][1] == "curve":
        if collinear(ppt[1][0], p[1][0], npt[1][0]) == False:
            print()
            print("flag 1, NOT COLLINEAR, checking non-smooth")
            print(p)
            print(p[1])
            return
    # Only care about smooth points
    elif p[1][2] != True:
        print("flag 2")
        return
    # Only care about ⏺ points
    if check_circles == False and npt[1][1]==None and ppt[1][1]==None:
        print("flag 3")
        return
    # Only care about ▲ points
    if check_triangles == False and [npt[1][1], ppt[1][1]].count(None) == 1:
        print("flag 4")
        return
    
    if ppt[1][1]==None and p[1][1]=="curve" and npt[1][1]==None:
        apt = ppt
        bpt = p
        cpt = npt
    elif ppt[1][1]==None and p[1][1]=="curve" and npt[1][1] == "line":
        apt = ppt
        bpt = p
        cpt = npt
    elif pppt[1][1]==None and ppt[1][1]=="curve" and p[1][1]=="line" and npt[1][1]==None:
        apt = ppt
        bpt = p
        cpt = npt
    elif ppt[1][1] in ["curve", "line"] and p[1][1]=="line" and npt[1][1]==None:
        apt = ppt
        bpt = p
        cpt = npt

    if apt is not None and bpt is not None and cpt is not None:
        r = calc_ratio(apt[1][0], bpt[1][0], cpt[1][0])
        if r is not None:
            angle_1 = calc_angle(apt[1][0], bpt[1][0])
            angle_2 = calc_angle(bpt[1][0], cpt[1][0])
            angle = (angle_1 + angle_2) / 2  # math.atan2(apt[1][0][1] - cpt[1][0][1], apt[1][0][0] - cpt[1][0][0]) + .5 * math.pi
            angle_degrees = math.degrees(angle)
            
            return angle_degrees, r
    return None
        
        
def scan_fonts(fonts, angle_tol, ratio_tol, check_triangles=True, check_circles=True, check_non_smooth=False):
    base_f = fonts[0]
    all_info = {}
    for g_name in base_f.glyphOrder:
        # Debug with some glyphs
        debug = False
        if g_name in ["a"]:
            debug = True
        base_g = fonts[0][g_name]
        if not base_g.contours: continue
        all_point_info = []
        pen = RecordingPointPen() 
        base_g.drawPoints(pen) 
        point_info = reformat_pen_output(pen.value)
        if not point_info and debug:
            print(f"NO POINT INFO {g_name}")
            print("pen.value", pen.value)
            print("point_info", point_info)
            continue
        for c_i, c in enumerate(point_info):
            for p_i, p in enumerate(c):
                if get_angle_ratio(p, c, check_triangles, check_circles, check_non_smooth) == None:
                    continue
                angles, ratios = [], []
                for f in fonts:
                    if g_name not in f:
                        continue
                    check_pen = RecordingPointPen() 
                    f[g_name].drawPoints(check_pen) 
                    check_point_info = reformat_pen_output(check_pen.value)
                    if len(check_point_info) < c_i + 1:
                        continue
                    if len(check_point_info[c_i]) < p_i + 1:
                        continue
                    point_to_check = check_point_info[c_i][p_i]
                    if get_angle_ratio(point_to_check, check_point_info[c_i], check_triangles, check_circles, check_non_smooth) == None:
                        angle, ratio = None, None  # What should the failed value be?
                    else:
                        angle, ratio = get_angle_ratio(point_to_check, check_point_info[c_i], check_triangles, check_circles, check_non_smooth)
                        if debug: print("got angle", angle)
                    if angle is not None:
                        angles.append(angle)
                    if ratio is not None:
                        ratios.append(ratio)

                average_angle  = average_list(angles)%180
                average_ratio  = average_list(ratios)
                angle_gamut    = calc_angle_gamut(min(angles), max(angles))
                ratio_gamut    = round(max(ratios) - min(ratios), 2)
                quality_rating = calc_quality_score(angle_gamut, ratio_gamut, angle_tol, ratio_tol)

                if debug:
                    print(g_name, c_i, p_i), 
                    print("quality_rating", quality_rating)
                    print("angles", angles)
                    print("angle_gamut", angle_gamut)
                    print("average_angle", average_angle)
                    print("ratios", ratios)
                    print("ratio_gamut", ratio_gamut)
                    print("average_ratio", average_ratio)
                    print()

                all_info[(g_name, c_i, p_i)] = (quality_rating, angle_gamut, average_angle, ratio_gamut, average_ratio)    

    return all_info
            
                
