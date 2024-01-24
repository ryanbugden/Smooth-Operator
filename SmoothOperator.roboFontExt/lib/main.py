# menuTitle: Smooth Operator
# author:    Ryan Bugden

import ezui
from logic import scan_fonts
from mojo.UI import AllGlyphWindows, getGlyphViewDisplaySettings, setGlyphViewDisplaySettings
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.events import postEvent
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber, unregisterGlyphEditorSubscriber, registerSubscriberEvent, getRegisteredSubscriberEvents
import weakref
import merz


EXTENSION_KEY_STUB  = "com.ryanbugden.smoothOperator"
EVENT_KEY = EXTENSION_KEY_STUB + ".pointDidGetFlagged"


class Highlighter(Subscriber):
    
    debug = True
    controller = None
    
    tool_glyph_name = None
    contour_index   = None
    point_index     = None
    
    def build(self):
        self.glyph_editor = self.getGlyphEditor()
        self.ge_container = self.glyph_editor.extensionContainer(
                    identifier="highlighter", 
                    location="foreground", 
                    clear=True
                )
                
    def destroy(self):
        self.ge_container.clearSublayers()
        
    def glyphEditorDidSetGlyph(self, info):
        self.g = info['glyph']
        if self.g.name == self.tool_glyph_name:
            self.highlight_point(self.contour_index, self.point_index)
        
    glyphEditorGlyphDidChangeOutlineDelay = 0    
    def glyphEditorGlyphDidChangeOutline(self, info):
        self.highlight_point(self.contour_index, self.point_index)
            
    def pointDidGetFlagged(self, info):
        lle = info['lowLevelEvents'][0]
        self.tool_glyph_name, self.contour_index, self.point_index = lle['glyph_name'], lle['contour_index'], lle['point_index']
        self.getGlyphEditor().setGlyphByName(self.tool_glyph_name)
        self.g = RGlyph(self.getGlyphEditor().getGlyph())
        self.highlight_point(self.contour_index, self.point_index)
            
    def highlight_point(self, contour_index, point_index):
        self.ge_container.clearSublayers()
        if contour_index > len(self.g.contours) - 1:
            print("Smooth Operator: Contour index out of range")
            return
        if point_index > len(self.g.contours[contour_index].points) - 1:
            print("Smooth Operator: Point index out of range")
            return
        point = self.g.contours[contour_index].points[point_index]
        highlight = self.ge_container.appendSymbolSublayer(
                position=(point.x, point.y)
            )

        highlight.setImageSettings(
                dict(
                    name="star",
                    size=(32, 32),
                    fillColor=(1, 0, 0, 0.1),
                    strokeColor=(1, 0, 0, 1),
                    strokeWidth=2,
                    pointCount=8,
                )
            )
                

class SmoothOperator(ezui.WindowController):

    def build(self):
        content = """
        * HorizontalStack                      @mainHorzStack

        > * VerticalStack                      @leftVertStack

        >> !§ Source UFOs
        >> |---fonts---|                       @fontsTable
        >> |           |
        >> |-----------|

        >> * HorizontalStack
        >>> (Add Open UFOs)                    @addOpenFontsButton
        >>> (+-)                               @addRemoveButton

        >> ---

        >> * TwoColumnForm                     @settingsForm
        >>> : Tolerance:
        >>> [_1 _] Angle (°)                   @angleTolerance
        >>> [_0.3 _] Ratio                     @ratioTolerance
        >>> : Scan:
        >>> [X] Smooth Triangle Points         @triPointCheckbox
        >>> [X] Smooth Circle Points           @circPointCheckbox

        >> (Scan Points)                       @scanButton

        > ---

        > * VerticalStack
        >> !§ Results
        >> |-----|                             @resultsTable
        >> |     |
        >> |-----|
        
        >> * HorizontalStack
        >>> 0 results                          @resultCountLabel
        >>> Indexes:                           @indexesLabel
        >>> (Show All)                         @showIndexesButton
        >>> (Hide All)                         @hideIndexesButton
        """
        results_table_items = []
        settings_title_width = 100
        left_column_width = 300
        results_column_min_width = 15
        results_column_width = 80
        descriptionData = dict(
            mainHorzStack=dict(
                distribution='fillEqually',
            ),
            angleTolerance=dict(
                valueWidth = 40,
                valueType = 'float',
                valueIncrement = 0.1
            ),
            ratioTolerance=dict(
                valueWidth = 40,
                valueType = 'float',
                valueIncrement = 0.1
            ),
            leftVertStack=dict(
                width=left_column_width
            ),
            settingsForm=dict(
                titleColumnWidth=settings_title_width,
                itemColumnWidth=left_column_width-settings_title_width
            ),
            fontsTable=dict(
                acceptedDropFileTypes=[".ufo"],
                allowsDropBetweenRows=True,
                allowsInternalDropReordering=True,
                width='fill',
                height='fill',
                columnDescriptions=[
                    dict(
                        identifier="familyName",
                        title="Family Name",
                        width=left_column_width/2
                    ),
                    dict(
                        identifier="styleName",
                        title="Style Name"
                    )
                ]
            ),
            addRemoveButton=dict(
                gravity='trailing'
            ),
            scanButton=dict(
                width='fill'
            ),
            resultsTable=dict(
                width='fill',
                height='fill',
                items=results_table_items,
                allowsSorting=True,
                allowsMultipleSelection=False,
                columnDescriptions=[
                    dict(
                        identifier="glyph_name",
                        title="Glyph Name",
                        minWidth=20,
                        width=results_column_width + 20,
                        editable=False
                    ),
                    dict(
                        identifier="contour_index",
                        title="Contour",
                        minWidth=results_column_min_width,
                        width=results_column_width - 30,
                        editable=False
                    ),
                    dict(
                        identifier="point_index",
                        title="Point",
                        minWidth=results_column_min_width,
                        width=results_column_width - 30,
                        editable=False
                    ),
                    dict(
                        identifier="quality_rating",
                        title="Quality Rating",
                        minWidth=results_column_min_width,
                        width=results_column_width + 20,
                        cellDescription=dict(
                            cellType="LevelIndicator",
                            valueType="integer",
                            cellClassArguments=dict(
                                minValue=0,
                                maxValue=100
                            ),
                        ),
                        editable=False
                    ),
                    dict(
                        identifier="angle_gamut",
                        title="Angle Gamut",
                        minWidth=results_column_min_width,
                        width=results_column_width - 8,
                        editable=False
                    ),
                    dict(
                        identifier="average_angle",
                        title="Average Angle",
                        minWidth=results_column_min_width,
                        width=results_column_width,
                        editable=False
                    ),
                    dict(
                        identifier="ratio_gamut",
                        title="Ratio Gamut",
                        minWidth=results_column_min_width,
                        width=results_column_width - 10,
                        editable=False
                    ),
                    dict(
                        identifier="average_ratio",
                        title="Average Ratio",
                        minWidth=results_column_min_width,
                        editable=False
                    ),
                ]
                ),
                indexesLabel=dict(
                    gravity='trailing'
                ),
                showIndexesButton=dict(
                    width=80,
                    gravity='trailing',
                ),
                hideIndexesButton=dict(
                    width=80,
                    gravity='trailing',
                ),
        )
        self.w = ezui.EZWindow(
            content=content,
            title="Smooth Operator",
            descriptionData=descriptionData,
            controller=self,
            size=(1120, 600),
            minSize=(400, 300),
            defaultButton='scanButton',
        )
        # Set up relationship with Subscriber in order to highlight points of interest
        Highlighter.controller = self
        registerGlyphEditorSubscriber(Highlighter)
        # Reload previous settings
        self.settings_form = self.w.getItem("settingsForm")
        settings = getExtensionDefault(EXTENSION_KEY_STUB + ".settings", fallback=self.settings_form.getItemValues())
        try: self.settings_form.setItemValues(settings)
        except KeyError: pass
        self.result_count = self.w.getItem("resultCountLabel")
        self.result_count.show(False)
        self.fonts_table = self.w.getItem("fontsTable")
        self.results_table = self.w.getItem("resultsTable")
        
    def started(self):
        self.w.open()
        
    def destroy(self):
        setExtensionDefault(EXTENSION_KEY_STUB + ".settings", self.settings_form.getItemValues())
        unregisterGlyphEditorSubscriber(Highlighter)
        Highlighter.controller = None
        
    def reset_results(self):
        self.results_table.set({})
        self.result_count.show(False)
        self.result_count.set("0 results")
        
    def resultsTableSelectionCallback(self, sender):
        if not sender.getSelectedItems():
            return
        selected_g_name = sender.getSelectedItems()[0]['glyph_name']
        contour_index = sender.getSelectedItems()[0]['contour_index']
        point_index = sender.getSelectedItems()[0]['point_index']
        postEvent(EVENT_KEY, glyph_name=selected_g_name, contour_index=contour_index, point_index=point_index)
        
    def fontsTableCreateItemsForDroppedPathsCallback(self, sender, paths):
        fonts = [
            OpenFont(path, showInterface=False)
            for path in paths
        ]
        return fonts
        
    def showIndexesButtonCallback(self, sender):
        self.show_hide_indexes(True)
    def hideIndexesButtonCallback(self, sender):
        self.show_hide_indexes(False)
        
    def show_hide_indexes(self, on_off=True):
        display_settings = getGlyphViewDisplaySettings()
        display_settings['ContourIndexes'] = on_off
        display_settings['PointIndexes']   = on_off
        setGlyphViewDisplaySettings(display_settings)
        
    def addOpenFontsButtonCallback(self, sender):
        self.fonts = self.fonts_table.get()
        for font in AllFonts():
            if not font in self.fonts:
                self.fonts.append(font)
        self.fonts_table.set(self.fonts)
        
    def addRemoveButtonAddCallback(self, sender):
        value = "get font files here"
        self.fonts = self.fonts_table.get()
        self.fonts.append(value)
        self.fonts_table.set(self.fonts)

    def addRemoveButtonRemoveCallback(self, sender):
        self.fonts = self.fonts_table.get()
        for index in reversed(self.fonts_table.getSelectedIndexes()):
            del self.fonts[index]
        self.fonts_table.set(self.fonts)
        
    def scanButtonCallback(self, sender):
        self.fonts = self.fonts_table.get()
        angle_tol  = self.w.getItem("angleTolerance").get()
        ratio_tol  = self.w.getItem("ratioTolerance").get()
        triangles  = self.w.getItem("triPointCheckbox").get()
        circles    = self.w.getItem("circPointCheckbox").get()
        scanned_fonts = scan_fonts(self.fonts, angle_tol, ratio_tol, triangles, circles)
        # Sort the results with the worst quality rating first.
        scan_results_ordered = dict(sorted(scanned_fonts.items(), key=lambda item: item[1][0]))
        ## Figure out how to group by glyph name after sorting quality?
        self.reset_results()
        for (g_name, contour_index, point_index), (quality_rating, angle_gamut, average_angle, ratio_gamut, average_ratio) in scan_results_ordered.items():
            table_item = {
                "glyph_name":     g_name,
                "contour_index":  round(contour_index, 2),
                "point_index":    round(point_index, 2),
                "quality_rating": round(quality_rating, 2),
                "angle_gamut":    round(angle_gamut, 2),
                "average_angle":  round(average_angle, 2), 
                "ratio_gamut":    round(ratio_gamut, 2),
                "average_ratio":  round(average_ratio, 2),
                    }
            if quality_rating != 100:
                self.results_table.appendItems([table_item])
        result_count = len(self.results_table.get())
        if result_count > 0:
            self.result_count.set(f"{len(self.results_table.get())} results")
        else:
            self.result_count.set("Looking smooth!")
        self.result_count.show(True)
        
        

if __name__ == "__main__":
    if EVENT_KEY not in getRegisteredSubscriberEvents():
        registerSubscriberEvent(
            subscriberEventName=EVENT_KEY,
            methodName="pointDidGetFlagged",
            lowLevelEventNames=[EVENT_KEY],
            # eventInfoExtractionFunction=demoInfoExtractor,
            dispatcher="roboFont",
            delay=0,
            debug=True
        )
    SmoothOperator()