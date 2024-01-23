import math
from fontParts.world import OpenFont

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
    return sum(lst) / len(lst) 
    
def calculate_quality_score(angle_gamut, ratio_gamut, angle_tol, ratio_tol):
    # Calculate the quality score
    if angle_gamut < angle_tol or ratio_gamut < ratio_tol:
        quality_score = 100
    else:
        quality_score = (-angle_tol * 10 * angle_gamut) + (-ratio_tol * 10 * ratio_gamut) + 100
    return quality_score
    
def get_angle_ratio(p, check_triangles, check_circles):
    i = p.index
    c = p.contour
    l = len(c.points)
    pppt = c.points[i-2]
    ppt = c.points[i-1]
    npt = c.points[(i+1)%l]
    nnpt = c.points[(i+2)%l]

    apt = bpt = cpt = r = rin = rout = None
    
    # Only care about smooth points
    if p.smooth != True:
        return
    # Only care about ⏺ points
    if check_circles == False and npt.type=="offcurve" and ppt.type=="offcurve":
        return
    # Only care about ▲ points
    if check_triangles == False and [npt.type, ppt.type].count("offcurve") == 1:
        return
    
    if ppt.type=="offcurve" and p.type=="curve" and npt.type=="offcurve":
        apt = ppt
        bpt = p
        cpt = npt
    elif ppt.type=="offcurve" and p.type=="curve" and npt.type == "line":
        apt = ppt
        bpt = p
        cpt = npt
    elif pppt.type=="offcurve" and ppt.type=="curve" and p.type=="line" and npt.type=="offcurve":
        apt = ppt
        bpt = p
        cpt = npt
    elif ppt.type in ["curve", "line"] and p.type=="line" and npt.type=="offcurve":
        apt = ppt
        bpt = p
        cpt = npt

    if apt is not None and bpt is not None and cpt is not None:
        rin = math.hypot(apt.x-bpt.x,apt.y-bpt.y)
        rout = math.hypot(cpt.x-bpt.x,cpt.y-bpt.y)
        r = rin / rout
    if r is not None:
        angle = math.atan2(apt.y-cpt.y,apt.x-cpt.x) + .5* math.pi
        angle_degrees = math.degrees(angle)%180
        
    return round(angle_degrees, 2), round(r, 2)
        
        
def scan_fonts(fonts, angle_tol, ratio_tol, check_triangles, check_circles):
    base_f = fonts[0]
    all_info = {}
    for g_name in base_f.glyphOrder:
        base_g = fonts[0][g_name]
        if not base_g.contours: continue
        all_point_info = []
        for c_i, c in enumerate(base_g.contours):
            for p_i, p in enumerate(c.points):
                if get_angle_ratio(p, check_triangles, check_circles) == None:
                    continue
                
                angles, ratios = [], []
                for f in fonts:
                    point_to_check = f[g_name][c_i].points[p_i]
                    if get_angle_ratio(point_to_check, check_triangles, check_circles) == None:
                        angle, ratio = 0, 0  # What should the failed value be?
                    else:
                        angle, ratio = get_angle_ratio(point_to_check, check_triangles, check_circles)
                    angles.append(angle)
                    ratios.append(ratio)
                
                average_angle  = average_list(angles)
                average_ratio  = average_list(ratios)
                angle_gamut    = max(angles) - min(angles)
                ratio_gamut    = max(ratios) - min(ratios)
                quality_rating = calculate_quality_score(angle_gamut, ratio_gamut, angle_tol, ratio_tol)
            
                all_info[(g_name, c_i, p_i)] = (quality_rating, angle_gamut, average_angle, ratio_gamut, average_ratio)    

    return all_info
            
                


