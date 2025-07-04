# Geoscience_section_vertical_exaggeration
qgis plugin to vertically exaggerate a geoscience cross section

Geoscience Section Vertical Exaggeratin – Plugin

1	Geoscience Plugin 
	Start by processing your data according to Roland Hill’s Geoscience Plugin. Testdata is availabe under: 
	https://github.com/rolandhill/geoscience/tree/master/testdata
	After having worked through the Geoscience Plugin workflow create a section using the Geoscience Plugin Section Manager.
	 
	By creating a South-North Section using East: 500050 and a South Limit 1999980 and North Limit 2000120 you get the following section.
	 
2	Geoscience Section Vertical Exaggeratin – Plugin
	After installation you can find the Geoscience Section Vertical Exaggeratin – Plugin under Plugins
	 
2.1	 Generate vertical section scale (at 1:1)
	The Geoscience – Plugin creates a grid. Depending on your project the interval might be too corse. When vertically exaggerating a scale you want to be sure to be in control of your vertical scale. Therefore you can create a vertical scale using the “Generate vertical section scale (at 1:1)” Tool.
	By clicking on it the following dialoge box opens
	 
	Provide your chosen values and click OK.

	It is important to create the vertical scale before the vertical exaggeration is executed in order to get the real values for the hight.
	Make sure, the newly created section scale layer is placed within the folder of the section (i.e. “500050E”).

	The position of the labels can be manipulated under the layer properties – Labels – Placement. Here you can also apply a horizont offset, if the X Position provided earlier is not where you would like it to be.

2.2	Apply vertical exaggeration (to group)
	Select the group in the layer tree that contains the section you are working on and click on the Apply vertical exaggeration (to group) Tool.
	 
	Enter the desired exaggeration factor into the dialog box and click OK.

	This creates a new group containing the vertically exaggerated layers as temporary copies.
	 
	Note that the vertical data now does not anymore correspond 1:1 to the y-axis value. The labels of the grid (generated by the Geoscience Plugin) and the Sections scale (generated by this Plugin) are still valid.

2.3	Make selected group permanent

	If the outcome satisfies your needs you can save the layers of the section group to a folder location by using the Make selected group permanent Tool.
	 
	This creates permanent duplicates of all the layers within the selected group.
	 

2.4	Remove and delete temporary features in selected group
	Make sure you have all the needed layers permanent and all the symbology is copied properly to the new layers. After that you can delete the temporary layers from the section group by using the Remove and delete temporary features in selected group Tool.
	 
	Confirm the deletion.
	 

2.5	Print Layout

	When using the QGIS print layout composer, the scale of the map (under Map – Main Properties – Scale) indicates the horizontal scale. This scale is also represented by the scale bar.
	 
	The vertical scale is indicated only by the labels of the Geoscience Plugin Grid and the Section scale generated with this plugin.

	The grid of the map item would indicate the following given a 10m Y interval (map grid labels on the left):
	 
	Nevertheless, the map grid can be very helpful with unchecked “Draw Coordinates” and adjusted Y interval. 


