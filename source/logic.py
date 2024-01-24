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
    return sum(lst) / len(lst) 
    
def get_angle_gamut(angle_1, angle_2):
    gamut = abs(angle_2 - angle_1)
    if gamut > 180:
        gamut = 360 - gamut
    return gamut
    
def calculate_quality_score(angle_gamut, ratio_gamut, angle_tol, ratio_tol):
    # Calculate the quality score
    if angle_gamut < angle_tol or ratio_gamut < ratio_tol:
        quality_score = 100
    else:
        quality_score = (-angle_tol * 10 * angle_gamut) + (-ratio_tol * 10 * ratio_gamut) + 100
    return quality_score
    
def reformat_pen_output(pen_value):
    main_list = []
    new_list = []
    c_i, p_i = 0, 0
    for entry in pen_value:    
        if entry[0] == "beginPath":
            if not new_list == []:
                main_list.append(new_list)
            new_list = []
            p_i = 0
            continue
        elif entry[0] == "endPath" or entry[0] == ():
            c_i += 1
            continue
        new_list.append(((c_i, p_i), entry[1]))
        p_i += 1
    return main_list
    
def get_angle_ratio(p, contour_point_info, check_triangles, check_circles):
    i = p[0][1]
    c = contour_point_info
    l = len(contour_point_info)
    pppt = c[i-2]
    ppt = c[i-1]
    npt = c[(i+1)%l]
    nnpt = c[(i+2)%l]

    apt = bpt = cpt = r = rin = rout = None
    
    # Only care about smooth points
    if p[1][2] != True:
        return
    # Only care about ⏺ points
    if check_circles == False and npt[1][1]==None and ppt[1][1]==None:
        return
    # Only care about ▲ points
    if check_triangles == False and [npt[1][1], ppt[1][1]].count(None) == 1:
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
        rin = math.hypot(apt[1][0][0]-bpt[1][0][0],apt[1][0][1]-bpt[1][0][1])
        rout = math.hypot(cpt[1][0][0]-bpt[1][0][0],cpt[1][0][1]-bpt[1][0][1])
        r = rin / rout
    if r is not None:
        angle = math.atan2(apt[1][0][1]-cpt[1][0][1],apt[1][0][0]-cpt[1][0][0]) + .5* math.pi
        angle_degrees = math.degrees(angle)
        
    return round(angle_degrees, 2), round(r, 2)
        
        
def scan_fonts(fonts, angle_tol, ratio_tol, check_triangles, check_circles):
    base_f = fonts[0]
    all_info = {}
    for g_name in base_f.glyphOrder:
        base_g = fonts[0][g_name]
        if not base_g.contours: continue
        all_point_info = []
        pen = RecordingPointPen() 
        base_g.drawPoints(pen) 
        point_info = reformat_pen_output(pen.value)
        if not point_info:
            continue
        for c_i, c in enumerate(point_info):
            for p_i, p in enumerate(c):
                if get_angle_ratio(p, c, check_triangles, check_circles) == None:
                    continue
                angles, ratios = [], []
                for f in fonts:
                    check_pen = RecordingPointPen() 
                    f[g_name].drawPoints(check_pen) 
                    check_point_info = reformat_pen_output(check_pen.value)
                    if len(check_point_info) < c_i + 1:
                        continue
                    if len(check_point_info[c_i]) < p_i + 1:
                        continue
                    point_to_check = check_point_info[c_i][p_i]
                    if get_angle_ratio(point_to_check, check_point_info[c_i], check_triangles, check_circles) == None:
                        angle, ratio = 0, 0  # What should the failed value be?
                    else:
                        angle, ratio = get_angle_ratio(point_to_check, check_point_info[c_i], check_triangles, check_circles)
                    angles.append(angle)
                    ratios.append(ratio)

                average_angle  = average_list(angles)%180
                average_ratio  = average_list(ratios)
                angle_gamut    = get_angle_gamut(min(angles), max(angles))
                ratio_gamut    = max(ratios) - min(ratios)
                quality_rating = calculate_quality_score(angle_gamut, ratio_gamut, angle_tol, ratio_tol)

                all_info[(g_name, c_i, p_i)] = (quality_rating, angle_gamut, average_angle, ratio_gamut, average_ratio)    

    return all_info
            
                
