# Smooth Operator

<img src="./images/mechanic_icon.png"  width="80">

#### Smooth Operator is a RoboFont extension for diagnosing all angle/ratio discrepancies between interpolable UFOs. It basically helps prevent kinks in your curves. 

#### It was written on top of code from [Angle Ratio Tool](https://github.com/LettError/angleRatioTool) by Letterror/Erik van Blokland, and it is intended for use in conjunction with Angle Ratio Tool.

<img src="./images/ui.png">

## Sample workflow:
1. Get your type family to a place where it is actually interpolable/"Prepolated" (same start points, contour order, contour direction, etc.)
2. Run Smooth Operator in order to view problem-points, ranked by priority: low-quality angle/ratio (most likely to cause kinks in your interpolation) to high-quality (fairly synced angles and/or ratios across all sources).
3. Work your way down the rows, and use Angle Ratio Tool in Glyph Editor to manually address the issues, using your judgment based on your design (e.g. should I adjust the angle or the ratio?).


## UI

### Source UFOs
These are the UFOs that will be checked/scanned. They could be already-open UFOs (Add Open UFOs button), but they don’t have to be open at the time of scanning.

### Settings

##### Tolerance
When looking at individual points across all UFOs, if the difference in angles or ratios exceeds these threshols, they will be given some quality rating below 100%. The default tolerances are `1` for Angle and `0.3` for Ratio—in this case, points with an angle gamut of less that 1 and a ratio gamut of less than 0.3 will not be shown in the Results table.

##### Check Points
Choose the type of points you'd like to evaluate. Only points with a `smooth` flagged will be checked. Triangle points are smooth points with only one off-curve. Circle points are smooth points with two off-curves.

### Results
This is the output of the tool, allowing you to see which specific points might cause issues in your interpolation. When you click on a row, all open glyph windows will not only go to the that glyph, but also mark the problem point with a red star.

##### Indexes
Using these buttons, you can globally control the display settings of all open glyph windows, either showing or hiding all labels for contour or point indexes. This is useful if you don’t want to click each row, and instead want to just manually go through points yourself. 
