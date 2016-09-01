import os
import arcpy
import sys

from config import *


class LayoutTableError(Exception):
    def __init__(self, message, **errors):
        super(LayoutTableError, self).__init__(message)
        self.errors = errors


class LayoutTable:
    def __init__(self, mxd=None, SP=None):
        """
        Create new LayoutTable instance for a specific map document.
        :param mxd: Path to the map document
        :param SP: gsdfgsdg
        :return: None
        """

        if not mxd:
            self.mxd = arcpy.mapping.MapDocument("current")
        try:
            if isinstance(mxd, str):
                # assert os.path.exists(mxd)
                self.mxd = arcpy.mapping.MapDocument(mxd)
            elif isinstance(mxd, arcpy.mapping.MapDocument):
                self.mxd = mxd

            self.base_element = \
                arcpy.mapping.ListLayoutElements(self.mxd, "TEXT_ELEMENT", BASE_ELEMENT_NAME)[0]
            self.header_base_element = \
                arcpy.mapping.ListLayoutElements(self.mxd, "TEXT_ELEMENT", HEADER_BASE_ELEMENT_NAME)[0]
        except IndexError:
            raise LayoutTableError("Base layout element for cell or header was not found in the map document.")
        except AssertionError as e:
            print e.message
            raise sys.exit(1)
        self.SP = SP

        self.COL_SPACE = self.base_element.elementWidth
        self.ROW_SPACE = self.base_element.elementHeight

    def _create_cell(self, text, column, row):
        new_element = self.base_element.clone("_{}_{}".format(column, row))
        new_element.elementPositionX += column * self.COL_SPACE
        new_element.elementPositionY -= row * self.ROW_SPACE
        try:
            text = "{:.2f}".format(text)
        except:
            pass
        print text,
        new_element.text = u"{}".format(text)

    def _create_header(self, text, column):
        new_element = self.header_base_element.clone("_{}".format(column))
        new_element.elementPositionX += column * self.COL_SPACE
        text = u"{}".format(LayoutTable.fix_col_name(text))
        print text
        new_element.text = text

    def create_table(self, fc, fields):
        """
        Create the table in the map document layout, using data from the specified fields of a feature class.
        :param fc: The feature class
        :param fields: List of fields names to be included in the layout table
        :return: None
        """
        self.delete_all()
        for f in fields:
            self._create_header(f, fields.index(f))
        row, col = 0, 0

        if self.SP:
            where_clause = "\"SP\"='{}'".format(self.SP)
        else:
            where_clause = ""
        with arcpy.da.SearchCursor(fc, fields, where_clause) as cursor:
            for feature in cursor:
                for data in feature:
                    try:
                        self._create_cell(data, col, row)
                    except Exception as err:
                        print err
                    col += 1
                row += 1
                col = 0
                print ""
        self.base_element.text = " "
        self.header_base_element.text = " "
        self.mxd.save()

    def delete_all(self, hide_base=False):
        for wildcard in ["cell_*", "header_*"]:
            elements = arcpy.mapping.ListLayoutElements(self.mxd, "TEXT_ELEMENT", "{}".format(wildcard))
            for e in elements:
                e.delete()
            self.base_element.text = "BASE"
            self.header_base_element.text = "HEADER"
        if hide_base:
            self.base_element.text = " "
            self.base_element.elementPositionX = -20
            self.header_base_element.text = " "
            self.header_base_element.elementPositionX = -20

        arcpy.RefreshActiveView()

    @staticmethod
    def fix_col_name(name):
        alias = {"SHAPE.STLENGTH()": "Length (m)",
                 "SHAPE@LENGTH": "Length (m)",
                 "ANGLE": "Bearing",
                 "ENDX": "Easting",
                 "ENDY": "Northing",
                 "FROMNAME": "From Beacon",
                 "TONAME": "To Beacon"
                 }
        try:
            return alias[name.upper()]
        except KeyError:
            return name

    def tdp_table(self):
        try:
            self.create_table('tdp_lines', ["FromName", "EndX", "EndY", "Angle", "Shape.STLength()", "ToName"])
        finally:
            self.base_element.text = " "
            self.header_base_element.text = " "
