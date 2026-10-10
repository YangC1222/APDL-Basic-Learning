# 2026-10-10 · 燃料/控制棒关键参数扫描与结果批量导出

## 今日目标
同时改变生热、导热率和对流边界，逐工况导出可追溯全场与验证表。

## 物理问题
等效轴对称圆柱，R=4 mm、L=40 mm，SI单位m/W/K。均匀体积热源，两端绝热、外壁对流、Tb=573 K、常导热率；不包含真实包壳、间隙、接触、辐照、相变或应力。教学参数不能作为反应堆安全输入。

## 关键命令
- PLANE55、KEYOPT(3)=1：轴对称热模型，以完整360°圆柱解释功率。
- *DIM：固定空间映射与五个参数快照。
- *GET,NXTH：按实际节点号遍历，避免假定节点编号连续。
- MP,KXX、BFE,HGEN、SF,CONV：分别更新导热率、体积热源、对流；每次覆盖前一工况。
- ANTYPE,STATIC,NEW：各参数独立求解；不能在循环中/CLEAR删除数组。
- SET,LAST和*GET,TEMP：从本次结果提取节点温度；不存在NODE,0,MAX,TEMP写法。
- *VLEN,1及*VWRITE：逐行导出八列、保留纯格式行。

## 完整脚本
```apdl
/CLEAR,NOSTART ! 只在循环前清理独立模型；m、W、K单位制
/FILNAME,lesson28 ! 本课前缀
/PREP7 ! 建立固定网格热模型
ET,1,PLANE55 ! 四节点热单元
KEYOPT,1,3,1 ! 轴对称，X为径向、Y为轴向
rad=0.004 ! 半径4 mm
alen=0.040 ! 长度40 mm
tbulk=573 ! 冷却剂温度K
kcond=3 ! 等效燃料导热率W/(m K)
MP,KXX,1,kcond ! 常导热教学材料，不含包壳或间隙
RECTNG,0,rad,0,alen ! 圆柱子午面
MSHKEY,1 ! 映射网格
MSHAPE,0,2D ! 四边形网格
ESIZE,0.0005 ! 名义网格尺寸0.5 mm
AMESH,ALL ! 只划分一次，所有快照节点顺序相同
ALLSEL,ALL ! 节点统计前恢复全部选择
*GET,nnodes,NODE,0,COUNT ! 节点总数
*DIM,snap,ARRAY,nnodes,8 ! 节点号、r、z与五个参数工况温度
*DIM,res,ARRAY,5,8 ! q、k、h、中心、外壁、解析中心、温升误差、热平衡误差
prevnode=0 ! 节点号从0之后开始查找
*DO,ii,1,nnodes ! 保存真实选中节点编号，允许编号不连续
*GET,nownd,NODE,prevnode,NXTH ! 获取下一更大选中节点号
snap(ii,1)=nownd ! 保存节点号，不能用数组行号替代
snap(ii,2)=NX(nownd) ! 保存径向坐标m
snap(ii,3)=NY(nownd) ! 保存轴向坐标m
prevnode=nownd ! 更新遍历位置
*ENDDO ! 完成节点映射
FINISH ! 完成固定模型
*DO,icase,1,5 ! 五个独立参数点，保持几何与节点一致
qvol=1E8+icase*2E7 ! 生热依次1.2至2.0E8 W/m3
hcoef=20000 ! 外面对流W/(m2 K)
kcond=3+3*(icase-1) ! 教学材料导热率3、6、9、12、15 W/(m K)
hcoef=10000+2500*(icase-1) ! 教学对流10000至20000 W/(m2 K)
/PREP7 ! 更新材料与热载荷
MP,KXX,1,kcond ! 当前参数的常导热率
ALLSEL,ALL ! 热源施加全部单元
BFE,ALL,HGEN,,qvol ! 覆盖前一工况体积热源
NSEL,S,LOC,X,rad ! 选外壁节点
SF,ALL,CONV,hcoef,tbulk ! 覆盖当前工况外壁对流，端面自然绝热
ALLSEL,ALL ! 求解前恢复所有选择
FINISH ! 完成载荷更新
/SOLU ! 稳态导热分析
ANTYPE,STATIC,NEW ! 当前参数新分析，数组保留
OUTRES,ALL,ALL ! 保存温度
SOLVE ! 求解本参数点
FINISH ! 完成求解
/POST1 ! 读取结果
SET,LAST ! 本次结果
ALLSEL,ALL ! 保存所有节点温度
*DO,ii,1,nnodes ! 按已保存节点映射提取
nownd=snap(ii,1) ! 真实节点号
*GET,tnow,NODE,nownd,TEMP ! 本节点温度K
snap(ii,icase+3)=tnow ! 对应参数列
*ENDDO ! 完成全场快照
ncenter=NODE(0,alen/2,0) ! 轴线中点
nouter=NODE(rad,alen/2,0) ! 外壁中点
*GET,tc,NODE,ncenter,TEMP ! 中心温度K
*GET,to,NODE,nouter,TEMP ! 外壁温度K
texact=tbulk+qvol*rad/(2*hcoef)+qvol*rad**2/(4*kcond) ! 解析中心温度K
res(icase,1)=qvol ! 生热参数
res(icase,2)=kcond ! 导热率
res(icase,3)=hcoef ! 对流边界
res(icase,4)=tc ! 数值中心温度
res(icase,5)=to ! 数值外壁温度
res(icase,6)=texact ! 解析参考温度，非数值结果
res(icase,7)=ABS(tc-texact)/(texact-tbulk) ! 温升相对误差
res(icase,8)=ABS(hcoef*2*rad*(to-tbulk)-qvol*rad**2)/(qvol*rad**2) ! 轴向均匀时热平衡误差
FINISH ! 结束当前工况
*ENDDO ! 完成五个参数点
*CFOPEN,parameter_check,csv ! 参数及验证指标输出
*DO,ii,1,5 ! 逐工况一行
*VLEN,1 ! 避免自动向量重复输出
*VWRITE,res(ii,1),res(ii,2),res(ii,3),res(ii,4),res(ii,5),res(ii,6),res(ii,7),res(ii,8) ! 下一行纯格式，八列
(E13.6,7(',',E13.6))
*ENDDO ! 完成验证表
*CFCLOS ! 关闭参数表
*CFOPEN,field_snapshots,csv ! 节点号、r、z、五列完整温度场
*DO,ii,1,nnodes ! 按固定节点顺序逐行输出
*VLEN,1 ! 本次只写一行
*VWRITE,snap(ii,1),snap(ii,2),snap(ii,3),snap(ii,4),snap(ii,5),snap(ii,6),snap(ii,7),snap(ii,8) ! 下一行纯格式
(E13.6,7(',',E13.6))
*ENDDO ! 完成空间快照输出
*CFCLOS ! 关闭空间快照
FINISH ! 批处理结束
```

## 预期结果
公式：Ts=Tb+qR/(2h)；Tc=Ts+qR²/(4k)。固定k=3、h=20000时，q=1.2–2.0e8对应解析Tc=745.0–859.667 K。参数扫描工况则逐行使用表内k/h求解析值，不套用固定k参考范围。这些是解析参考值，本次实际求解数值与误差见下文验证状态。
field_snapshots.csv应为节点数行、8列：node,r,z,T1…T5；parameter_check.csv应5行8列：q,k,h,Tc,Ts,Tc_exact,err_dT,err_balance。保持各列与参数表对应。最大/平均两个标量不能充当完整空间快照。

## 验证清单
- 单位和轴对称360°热功率一致；检查外壁选择与两端自然绝热。
- 解析温升和热平衡逐工况对照，误差不以绝对K归一化掩盖。
- 至少用第27课三网格结果确定当前网格是否够用，再生成训练快照。
- CSV节点号/坐标固定，列数和工况一致；缺结果时不得构造“求解成功”的温度场。
- POD在外部建立时，按有限元质量或轴对称体积加权；当前脚本未训练、未投影、未提供在线ROM。只改变线性热源可能得到近似秩1温升快照，不用于证明通用POD能力。

## 常见错误
1. 在*DO内部/CLEAR：删除循环参数及数组；模型仅建立一次。
2. 将包壳/间隙赋同一材料：本课明确使用无包壳等效棒，真实分区需逐区赋材和界面核验。
3. 只有中心或平均温度就声称完成POD：输出全空间快照、元数据及独立验证；能量99%不是热点误差保证。

## 练习题
参数练习：留出中间参数工况，计算温升、峰值及守恒误差。反应堆扩展：加入控制棒k=15的等效材料另建数据库，不混淆材料号；在真实燃料—包壳接触模型中增加状态标签及外推回退。


本课五点为示范路径扫描，三个参数同时变化会混淆单参数因果；研究扫描应扩展为正交/全因子设计，并单列燃料与吸收体材料，不能声称这五点覆盖整个三维参数空间。


## 实际求解验证

本次隔离MAPDL求解返回0，无求解错误。验证表为5行8列，空间快照为729行8列，节点编号/坐标唯一且固定；逐工况温度场、轴向均匀性和外壁边界均已核对。最大中心温升相对解析误差 0.9157%，求解器保留精度下最大整体热平衡误差 1.14e-14。CSV温度输出有限小数位，重新用CSV算热平衡时应允许舍入误差。

| q（W/m³） | k（W/(m·K)） | h（W/(m²·K)） | 数值中心T（K） | 解析中心T（K） | 温升误差 |
| --- | --- | --- | --- | --- | --- |
| 1.20e+08 | 3 | 10000 | 758.685 | 757.000 | 0.916% |
| 1.40e+08 | 6 | 12500 | 689.716 | 688.733 | 0.849% |
| 1.60e+08 | 9 | 15000 | 666.193 | 665.444 | 0.810% |
| 1.80e+08 | 12 | 17500 | 654.203 | 653.571 | 0.784% |
| 2.00e+08 | 15 | 20000 | 646.895 | 646.333 | 0.766% |

0.5 mm网格对本课均匀常物性解析问题满足演示用1%温升误差限；第27课最后一次加密的燃料温升仍变化约2.27%，不能据此宣称严格网格独立。快照只验证数据准备，未训练或运行POD在线模型；线性恒物性温度剖面复杂度有限。

本地证据：validation/solver.out、上述CSV及validation/validation-summary.json。
