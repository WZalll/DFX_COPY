from logging import fatal
from typing import Any

from vSDK import *

PI = 3.141592653589793


def save_job():
    vSDK_SaveJob()


def vSDK_Board_UpdateLayerConfigFile(pcb):
    return vSDK_dll.vSDK_Board_UpdateLayerConfigFile(pcb, True)


def vSDK_DcodeTable_FindRectangleDcodeIDBySize(DcodeTable, CenterX: float, CenterY: float, Length: float, Width: float):
    DcodeID = ctypes.c_int(0)
    vSDK_dll.vSDK_DcodeTable_FindRectangleDcodeIDBySize(DcodeTable, ctypes.c_double(CenterX), ctypes.c_double(CenterY),
                                                        ctypes.c_double(Length), ctypes.c_double(Width),
                                                        ctypes.byref(DcodeID))
    return DcodeID


def vSDK_Shape_CreateArcOrPoints():
    ArcOrPoints = ctypes.c_void_p()
    vSDK_dll.vSDK_Shape_CreateArcOrPoints(ctypes.byref(ArcOrPoints))
    return ArcOrPoints

def delete_objects_from_layer(public_board, layer_id, obj_ids):
    """
    从指定层删除一组对象。
    :param public_board:    c_void_p，vSDK 返回的板对象句柄
    :param layer_id:        int，目标层 ID
    :param obj_ids:         list[int]，要删除的对象 ID 列表
    """
    # 创建 DeleteOrOffsetData 结构
    vycb_layer_objs = ctypes.c_void_p()
    ret = vSDK_dll.vSDK_Layer_Create_DeleteOrOffsetData(ctypes.byref(vycb_layer_objs))
    if ret != 1:
        raise RuntimeError(f"DeleteOrOffsetSelectobjsFromLayer 失败，错误码 {ret}")

    # 准备 C 数组
    count = len(obj_ids)
    IntArray = ctypes.c_int * count
    obj_array = IntArray(*obj_ids)

    # 填充要删除的对象 ID
    ret = vSDK_dll.vSDK_Layer_SetDeleteOrOffsetData(
        vycb_layer_objs,
        layer_id,
        obj_array,
        count
    )
    if ret != 1:
        raise RuntimeError(f"DeleteOrOffsetSelectobjsFromLayer 失败，错误码 {ret}")

    # 获取实际要删除的对象数（通常 == count）
    select_num = ctypes.c_int(-1)
    ret = vSDK_dll.vSDK_Layer_GetDeleteOrOffsetData_Count(
        vycb_layer_objs,
        ctypes.byref(select_num)
    )
    if ret != 1:
        raise RuntimeError(f"DeleteOrOffsetSelectobjsFromLayer 失败，错误码 {ret}")

    # 执行删除
    ret = vSDK_dll.vSDK_Layer_DeleteOrOffsetSelectobjsFromLayer(
        public_board,
        1,                 # mode=1 表示删除
        vycb_layer_objs,
        select_num.value,  # 实际数量
        0,0,0,0,0,0,0      # 其余保留参数填 0
    )
    if ret != 1:
        raise RuntimeError(f"DeleteOrOffsetSelectobjsFromLayer 失败，错误码 {ret}")

    return select_num.value


class ShapeEditor:
    def __init__(self, sdk_path: bytes, job_path: bytes):
        """

        :param sdk_path: vsdk.dll 所在folder
        :param job_path: vayo job 绝对路径
        """
        vSDK_Init(sdk_path)
        self.job = vSDK_OpenJob(job_path)
        self.pcb = vSDK_Job_GetCurrentPcb(self.job)
        self.board = vSDK_Pcb_GetBoard(self.pcb)

    def add_layer(self, layer_name: str, layer_side: bool):
        """
        添加一个层，如果存在同名层，则覆盖
        :param layer_name: 层面
        :param layer_side: True为正面，False为反面
        :return: 层id,层对象指针
        """
        layer = None
        layer_name = layer_name.encode()
        layer = vSDK_Board_GetLayerByName(self.board, layer_name)
        # 如果layer已经存在，则覆盖
        if layer.value:
            vSDK_Board_DeleteLayer(self.board, layer_name)
        layer = vSDK_Board_AddLayer(self.board, layer_name)
        layer_id = vSDK_Layer_GetLayerID(layer)
        if layer_side:
            vSDK_Layer_SetLayerSide(layer, 1)
        else:
            vSDK_Layer_SetLayerSide(layer, 3)
        vSDK_Board_UpdateLayerConfigFile(self.pcb)
        return layer_id.value, layer

    def delete_layer(self, layer_name: str):
        layer_name = layer_name.encode()
        layer = vSDK_Board_GetLayerByName(self.board, layer_name)
        if layer.value:
            vSDK_Board_DeleteLayer(self.board, layer_name)

    def delete_odj(self,layer_id,objs):
        delete_objects_from_layer(self.board, layer_id, objs)

    def get_layer_data(self) -> list:
        """
        获取全部layer信息

        :return: 包含全部layer信息的list
        """
        layer_count = vSDK_Board_GetLayerListCount(self.board)
        all_layer_data = []
        for index in range(0, layer_count.value):
            layer = vSDK_Board_GetLayerByIndex(self.board, index)
            layer_id = vSDK_Layer_GetLayerID(layer).value
            layer_name = vSDK_Layer_GetLayerName(layer).value
            layer_side = vSDK_Layer_GetLayerSide(layer).value
            layer_type = vSDK_Layer_GetLayerType(layer).value
            layer_thickness = vSDK_Layer_GetLayerThickness(layer).value
            resh_thickness = vSDK_Layer_GetReshThickness(layer).value
            positive = vSDK_Layer_GetPositive(layer).value
            all_layer_data.append((layer_id, layer_name, layer_side, layer_type, layer_thickness, resh_thickness,
                                   positive))
        return all_layer_data

    def get_part_data(self) -> list:
        """
        获取全部part信息

        :return: 包含全部part信息的list
        """
        iCount = vSDK_Board_GetPartListCount(self.board)
        part_data_list = []
        for id in range(0, iCount.value):
            part = vSDK_Board_GetPartByIndex(self.board, id)
            part_data = vSDK_Part_GetPartData(part)
            # PartID, PartName, PartPosX, PartPosY, PartAngle, Mirror, PinCount, PackageID, PackageName, PkgType, LayerName, LayerSide, CadPN, BomPN, InBom, PlaceMode, CadShapeName, BomPartName, BomCheckType, BomMainPnIndex
            part_data_list.append((
                part_data[0].value, part_data[1].value, part_data[2].value, part_data[3].value, part_data[4].value,
                part_data[5].value, part_data[6].value, part_data[7].value, part_data[8].value, part_data[9].value,
                part_data[10].value, part_data[11].value, part_data[12].value, part_data[13].value, part_data[14].value,
                part_data[15].value, part_data[16].value, part_data[17].value, part_data[18].value,
                part_data[19].value))
        return part_data_list

    def GetDcodeCountByLayerId(self, layerId: int):
        DcodeCount, DcodeTable = vSDK_Layer_GetDcodeCountByLayerId(self.board, layerId)
        return DcodeCount, DcodeTable

    def circle(self, circleX: float, circleY: float, circleDiameter: float, layerId: int,
               circlePositiveNegative: bool = True, circleFilled: bool = True
               ) -> int:
        """
        向图层添加圆形
        :param circleX: 圆心X坐标
        :param circleY: 圆心Y坐标
        :param circleDiameter: 圆形直径
        :param layerId: 要添加图形的层的ID
        :param circlePositiveNegative: 图形为正片还是负片 (True表示正片)
        :param circleFilled: 图形是否填充 (True表示填充)
        :return: 返回新增图形的ObjectID
        """
        if not circleFilled:
            return self.arc(circleX, circleY, circleDiameter / 2, 0, 2 * PI, layerId)

        DcodeCount, DcodeTable = self.GetDcodeCountByLayerId(layerId)
        circleShape = vSDK_Shape_CreateShapeByCircle(0, 0, circleDiameter,
                                                     circlePositiveNegative, circleFilled)
        if DcodeCount == 0:
            DcodeName = ("Circle" + str(circleDiameter)).encode()
            DCode = vSDK_Dcode_CreateDcode(DcodeTable, DcodeName, DcodeName)
            vSDK_Dcode_AddDcodeShape(DcodeTable, DCode, circleShape)
            DcodeID = vSDK_Dcode_AddDcodeEnd(DcodeTable, DCode)
        else:
            DcodeID = vSDK_DcodeTable_FindRoundDcodeIDBySize(DcodeTable, 0, 0, circleDiameter)
            if DcodeID.value < 0:
                DcodeName = ("Circle" + str(circleDiameter)).encode()
                DCode = vSDK_Dcode_CreateDcode(DcodeTable, DcodeName, "1".encode())
                vSDK_Dcode_AddDcodeShape(DcodeTable, DCode, circleShape)
                DcodeID = vSDK_Dcode_AddDcodeEnd(DcodeTable, DCode)
        layerObjectId = vSDK_Layer_AddShapeByDcode(self.board, layerId, 0, 0,
                                                   0, DcodeID, circlePositiveNegative, circleX,
                                                   circleY)
        vSDK_Shape_DestroyShape(circleShape)
        return layerObjectId.value

    def rectangle(self, CenterX: float, CenterY: float, Length: float, Width: float, layerId: int,
                  PositiveNegative=True, Filled=True) -> int:
        """
        向图层添加矩形
        :param CenterX: 矩形中心X
        :param CenterY: 矩形中心Y
        :param Length: 长
        :param Width: 宽
        :param layerId: 要添加图形的层的ID
        :param PositiveNegative: 正片/负片（True为正片）
        :param Filled: 填充状态（True为填充）
        :return: 返回新增图形的ObjectID
        """
        if not Filled:
            self.line(CenterX + (Length / 2), CenterY + (Width / 2), CenterX + (Length / 2), CenterY - (Width / 2),
                      layerId)
            self.line(CenterX + (Length / 2), CenterY - (Width / 2), CenterX - (Length / 2), CenterY - (Width / 2),
                      layerId)
            self.line(CenterX - (Length / 2), CenterY - (Width / 2), CenterX - (Length / 2), CenterY + (Width / 2),
                      layerId)
            self.line(CenterX - (Length / 2), CenterY + (Width / 2), CenterX + (Length / 2), CenterY + (Width / 2),
                      layerId)
            return -1

        DcodeCount, DcodeTable = self.GetDcodeCountByLayerId(layerId)
        shape = vSDK_Shape_CreateShapeByRectangle(0, 0, Length, Width, PositiveNegative, Filled)
        if DcodeCount == 0:
            DcodeName = ("Rectangle" + str(CenterX) + str(CenterY) + str(Length) + str(Width)).encode()
            DCode = vSDK_Dcode_CreateDcode(DcodeTable, DcodeName, DcodeName)
            vSDK_Dcode_AddDcodeShape(DcodeTable, DCode, shape)
            vSDK_Dcode_AddDcodeEnd(DcodeTable, DCode)
        DcodeID = vSDK_DcodeTable_FindRectangleDcodeIDBySize(DcodeTable, 0, 0, Length, Width)
        if DcodeID.value < 0:
            DcodeName = ("Rectangle" + str(CenterX) + str(CenterY) + str(Length) + str(Width)).encode()
            DCode = vSDK_Dcode_CreateDcode(DcodeTable, DcodeName, DcodeName)
            vSDK_Dcode_AddDcodeShape(DcodeTable, DCode, shape)
            DcodeID = vSDK_Dcode_AddDcodeEnd(DcodeTable, DCode)
        layerObjectId = vSDK_Layer_AddShapeByDcode(self.board, layerId, 0, 0,
                                                   0, DcodeID, PositiveNegative, CenterX,
                                                   CenterY)
        vSDK_Shape_DestroyShape(shape)
        return layerObjectId.value

    def line(self, StartX: float, StartY: float, EndX: float, EndY: float, layerId: int, LineLength=0.01,
             LineWidth=0.01, isRectangle=True,
             PositiveNegative=True, Filled=True) -> int:
        """
        向图层添加线
        :param StartX: 线段起点X轴坐标
        :param StartY: 线段起点Y轴坐标
        :param EndX: 线段终点X轴坐标
        :param EndY: 线段终点Y轴坐标
        :param layerId: 要添加图形的层的ID
        :param LineLength: 线长(矩形线头使用)
        :param LineWidth: 线宽(矩形线头使用)
        :param isRectangle: 是否为矩形线头(False则为圆形线头)
        :param PositiveNegative: 图形为正片还是负片(True为正片)
        :param Filled: 图形是否填充(True为填充)
        :return: 返回新增图形的ObjectID
        """
        lineShape = vSDK_Shape_CreateShapeByLine(StartX, StartY, EndX, EndY,
                                                 LineLength, LineWidth, isRectangle, PositiveNegative,
                                                 Filled)
        lineLayerObjectID = vSDK_Layer_AddShapeByLine(self.board, layerId, 0, lineShape)
        vSDK_Shape_DestroyShape(lineShape)
        return lineLayerObjectID.value

    def arc(self, CenterX: float, CenterY: float, Radius: float, StartAngle: float, AngleRotate: float, layerId: int,
            LineLength: float = 0.01, LineWidth: float = 0.01, isRectangle: bool = True, PositiveNegative: bool = True,
            Filled: bool = True) -> int:
        """
        向图层添加弧线
        :param CenterX: 弧形圆心X轴坐标
        :param CenterY: 弧形圆心Y轴坐标
        :param Radius: 弧形半径
        :param StartAngle: 起始弧度
        :param AngleRotate: 旋转弧度
        :param layerId: 要添加图形的层的ID
        :param LineLength: 线长(矩形线头使用)
        :param LineWidth: 线宽(矩形线头使用)
        :param isRectangle: 是否为矩形线头(False则为圆形线头)
        :param PositiveNegative: 图形为正片还是负片(True为正片)
        :param Filled: 图形是否填充(True为填充)
        :return: 返回新增图形的ObjectID
        """

        arcShape = vSDK_Shape_CreateShapeByArc(CenterX, CenterY, Radius, StartAngle,
                                               AngleRotate, LineLength, LineWidth, isRectangle,
                                               PositiveNegative, Filled);
        arcLayerObjectID = vSDK_Layer_AddShapeByArc(self.board, layerId, 0, arcShape)
        vSDK_Shape_DestroyShape(arcShape)
        return arcLayerObjectID.value

    def polygon(self, point_list, layerId: int, PositiveNegative: bool = True,
                Filled: bool = True) -> int:
        """
        向图层添加多边形
        :param point_list: 点列表,起始点与末尾点会自动连接,示例:[(10, -2), (12, -2), (14, -4), (12, -6), (10, -6), (8, -4)]
        :param layerId: 要添加图形的层的ID
        :param PositiveNegative: 图形为正片还是负片(True为正片)
        :param Filled: 图形是否填充(True为填充)
        :return: 返回新增图形的ObjectID
        """
        if not Filled:
            for index, point in enumerate(point_list):
                self.line(point_list[index][0], point_list[index][1], point_list[index - 1][0],
                          point_list[index - 1][1], layerId)
            return -1

        iArcOrPoint = vSDK_Shape_CreateArcOrPoints()
        pointCount = 0
        for point in point_list:
            pointCount = vSDK_Shape_AddArcOrPoint(iArcOrPoint, point[0], point[1], 0, 0, 0)
        ploygonShape = vSDK_Shape_CreateShapeByPolygon(iArcOrPoint, pointCount, PositiveNegative, Filled)
        ploygonLayerObjectID = vSDK_Layer_AddShapeByPolygon(self.board, layerId, 0, 0, ploygonShape)
        vSDK_Shape_DestroyShape(ploygonShape)
        return ploygonLayerObjectID.value

    def get_shape_data(self) -> list:
        """
        获取全部图形信息

        :return: 包含全部图形信息的list
        """
        layer_count = vSDK_Board_GetLayerListCount(self.board).value
        all_shapes_data = []
        for iLayerID in range(layer_count):
            vSDK_Layer_LoadLayerByLayerID(self.board, iLayerID)
            iObjCount = vSDK_Layer_GetLayerObjectCount(self.board, iLayerID).value
            for i in range(iObjCount):
                vSDK_Layer_GetLayerObjectPositive(self.board, iLayerID, i)
                iShapeCount = vSDK_Layer_GetLayerObjectShapeCount(self.board, iLayerID, i).value
                for k in range(iShapeCount):
                    shape = vSDK_Layer_GetLayerObjectShapeByIndex(self.board, iLayerID, i, k)[3]
                    sShapeType = vSDK_Shape_GetShapeType(shape).value
                    shapedata = self._get_shape_data_by_type(shape, sShapeType)
                    # all_shapes_data.append((shape, shapedata))
                    all_shapes_data.append(shapedata)
                    if shape is not None:
                        vSDK_Shape_DestroyShape(shape)
        return all_shapes_data

    def _get_shape_data_by_type(self, shape, sShapeType):
        """
        getshapedata的工具函数，private

        :param shape:
        :param sShapeType:
        :return:
        """
        if sShapeType == b"Circle":
            circle = vSDK_Shape_GetShapeDataByCircle(shape)
            return (circle[0].value, circle[1].value, circle[2].value, circle[3].value, circle[4].value)
        elif sShapeType == b"Rectangle":
            rectangle = vSDK_Shape_GetShapeDataByRectangle(shape)
            return (rectangle[0].value, rectangle[1].value, rectangle[2].value, rectangle[3].value, rectangle[4].value,
                    rectangle[5].value)
        elif sShapeType == b"Line":
            line = vSDK_Shape_GetShapeDataByLine(shape)
            return (
                line[0].value, line[1].value, line[2].value, line[3].value, line[4].value, line[5].value, line[6].value,
                line[7].value, line[8].value)
        elif sShapeType == b"Arc":
            arc = vSDK_Shape_GetShapeDataByArc(shape)
            return (arc[0].value, arc[1].value, arc[2].value, arc[3].value, arc[4].value, arc[5].value, arc[6].value,
                    arc[7].value, arc[8].value, arc[9].value)
        return None


if __name__ == '__main__':
    # sdk_path = b"D:/VayoPro/DFX MetaLab_20241230"  # DFX MetaLab的安装目录
    sdk_path = b"D:/VayoPro/DFX MetaLab_20250610_2/"  # DFX MetaLab的安装目录
    job_path = b"D:/VayoPro/DFX MetaLab_20241230/Data/education.vayo/education.job"  # vayo工程文件
    shape_editor = ShapeEditor(sdk_path, job_path)

    layer_id, layer = shape_editor.add_layer("test", True)
    # layer_id2, layer2 = shape_editor.add_layer("test2", True)
    # shape_editor.delete_layer("test2")
    shape_editor.circle(1, 1, 0.8, layer_id, circleFilled=False)
    shape_editor.circle(10, 0, 10, layer_id, circleFilled=False)
    shape_editor.circle(10, 12, 10, layer_id, circleFilled=False)
    shape_editor.delete_odj(layer_id,[1,2])

    nums = list(range(1, 100))
    shape_editor.delete_odj(2,nums)
    # shape_editor.circle(1, 1, 0.8, layer_id2)
    # shape_editor.circle(10, 0, 10, layer_id2)
    # shape_editor.circle(10, 12, 10, layer_id2)
    # shape_editor.rectangle(5, 1, 6, 4, layer_id, Filled=False)
    # shape_editor.rectangle(10, 2, 6, 4, layer_id, Filled=False)
    # shape_editor.rectangle(5, 1, 6, 4, layer_id2)
    # shape_editor.rectangle(10, 2, 6, 4, layer_id2)
    # shape_editor.line(20, 0, 20, 20, layer_id)
    # shape_editor.arc(0, 0, 20, PI, -0.5 * PI, layer_id)
    # shape_editor.arc(20, 0, 20, 0,2 * PI, layer_id,10,0.01,True,True,True)
    # shape_editor.polygon([(10, -2), (12, -2), (14, -4), (12, -6), (10, -6), (8, -4), ], layer_id, Filled=False)
    # shape_editor.polygon([(10, -2), (12, -2), (14, -4), (12, -6), (10, -6), (8, -4), ], layer_id2)

    save_job()
