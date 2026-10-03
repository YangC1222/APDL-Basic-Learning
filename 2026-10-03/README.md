# 第23课：板型燃料元件的温度场与板弯曲

2026-10-03

## 今日目标

先解三维板厚方向温度场，再传递到实体结构模型计算热弯曲。

## 物理问题

100×30×2 mm均质等效板，下表面550 K、上表面650 K、侧面绝热，根部固支。材料为教学常数，不建真实燃料—包壳多层。零体热源的定温模型用于检验温度传递和弯曲，不替代发热燃料热设计。

## 关键命令

- **SOLID70**：热实体求解节点温度，映射六面体保证厚度至少两层。
- **D,TEMP**：上下表面定温；侧面默认绝热。
- **ETCHG,TTS**：转换为对应结构单元，保留节点与网格。
- **DDELE,TEMP**：转换前删除温度约束，不删除其他几何对象。
- **LDREAD,TEMP**：从独立rth文件读取第一载荷步节点温度，不能从结构rst误读。
- **NLGEOM/NSUBST**：考虑热弯曲几何效应，检查收敛步及反力。

## 完整脚本

```apdl
/CLEAR,NOSTART                 ! 独立教学模型；SI单位m、N、K、Pa
/FILNAME,lesson23_th            ! 热分析文件前缀
/PREP7                         ! 前处理
length0=0.10                   ! 板长m
width0=0.03                    ! 板宽m
thick0=0.002                   ! 板厚m
ET,1,SOLID70                   ! 八节点三维热实体
MP,KXX,1,16                    ! 等效导热率W/(m K)，非真实复合燃料
MP,EX,1,1.9e11                 ! 等效弹性模量Pa
MP,PRXY,1,0.30                 ! 泊松比
MP,ALPX,1,1.2e-5               ! 等效膨胀系数1/K
BLOCK,0,length0,0,width0,0,thick0 ! 创建板型燃料等效实体
ESIZE,0.001                    ! 一毫米网格，厚度约两层；可减半检查
MSHKEY,1                       ! 映射网格
MSHAPE,0,3D                    ! 三维六面体网格
VMESH,ALL                      ! 对板体划分网格
NSEL,S,LOC,Z,0                 ! 选板下表面
D,ALL,TEMP,550                 ! 下表面固定温度K
NSEL,S,LOC,Z,thick0            ! 选板上表面
D,ALL,TEMP,650                 ! 上表面固定温度K，形成弯曲驱动
ALLSEL,ALL                     ! 侧面无载荷即绝热
FINISH                         ! 结束前处理
/SOLU                          ! 热求解
ANTYPE,STATIC                  ! 稳态导热
SOLVE                          ! 求解热场
FINISH                         ! 结束热求解
/POST1                         ! 热后处理
SET,LAST                       ! 读取热结果
PLNSOL,TEMP                    ! 绘制温度场
*GET,ncount0,NODE,0,COUNT       ! 取得全模型节点数
*GET,nid0,NODE,0,NUM,MIN        ! 从最小节点编号开始遍历
tmin0=1e20                     ! 初始化温度下界K
tmax0=-1e20                    ! 初始化温度上界K
*DO,ii,1,ncount0               ! 遍历热结果节点
*GET,tval0,NODE,nid0,TEMP       ! 当前节点温度K
tmin0=MIN(tmin0,tval0)          ! 累计最低温度K
tmax0=MAX(tmax0,tval0)          ! 累计最高温度K
*GET,nid0,NODE,nid0,NXTH        ! 下一个已选择节点编号
*ENDDO                         ! 结束热结果遍历
*CFOPEN,thermal_range,csv       ! 打开温度校核文件
*VWRITE,tmin0,tmax0             ! 下一行为温度最小最大值CSV
(E20.10,',',E20.10)
*CFCLOS                        ! 关闭温度输出文件
FINISH                         ! 结束热后处理
/PREP7                         ! 转换为结构模型
DDELE,ALL,TEMP                 ! 删除温度约束，防止留在结构求解
ETCHG,TTS                      ! 将SOLID70转为对应结构单元SOLID185
NSEL,S,LOC,X,0                 ! 板根部节点
D,ALL,ALL,0                    ! 根部全自由度固支
ALLSEL,ALL                     ! 恢复全部节点
TREF,550                       ! 无热应变参考温度K
LDREAD,TEMP,1,,,,lesson23_th,rth ! 从热结果第一载荷步传递节点温度
FINISH                         ! 完成载荷转换
/FILNAME,lesson23_st            ! 独立结构结果前缀，保留热结果文件
/SOLU                          ! 结构求解器
ANTYPE,STATIC                  ! 热应力静力分析
NLGEOM,ON                      ! 计入几何非线性，需检查收敛
NSUBST,20,100,10               ! 初始、最大与最小子步数量
SOLVE                          ! 求解热弯曲与应力
FINISH                         ! 结束结构求解
/POST1                         ! 结构后处理
SET,LAST                       ! 读取最后收敛结果
PLNSOL,U,Z                     ! 显示法向弯曲位移m
PLNSOL,S,EQV                   ! 显示等效应力Pa，根部奇异峰值不作安全限值
PRRSOL,F                       ! 输出支承反力，检查平衡
*GET,ncount0,NODE,0,COUNT       ! 全部结构节点数
*GET,nid0,NODE,0,NUM,MIN        ! 从最小编号开始
uzmin0=1e20                    ! 初始化Z位移下界m
uzmax0=-1e20                   ! 初始化Z位移上界m
*DO,ii,1,ncount0               ! 遍历结构节点
*GET,uz0,NODE,nid0,U,Z         ! 节点Z方向位移m
uzmin0=MIN(uzmin0,uz0)          ! 累计最小Z位移m
uzmax0=MAX(uzmax0,uz0)          ! 累计最大Z位移m
*GET,nid0,NODE,nid0,NXTH        ! 下一个选择节点
*ENDDO                         ! 完成结构结果遍历
*CFOPEN,bending_range,csv       ! 打开弯曲校核文件
*VWRITE,uzmin0,uzmax0           ! 下一行为Z位移最小最大值CSV
(E20.10,',',E20.10)
*CFCLOS                        ! 关闭位移文件
FINISH                         ! 完成本课
```

## 预期结果

- 纯导热热场应接近T=550+100z/t，作为解析校核而非已计算结果。
- 线弹性自由板曲率估算为αΔT/t；固支根部与有限厚度会导致局部偏差。
- 根部应力集中需检查网格与约束，不将单个峰值直接作为材料安全限值。

## 验证清单

- 热场上下热流大小应相等、方向相反，侧面热流应接近零。
- 检查LDREAD后结构温度范围仍为550–650 K，参考温度550 K。
- 将网格减半并增加厚度层数，比较远离根部位移及应力。
- 检查所有子步收敛、支反力平衡以及根部固支定义。

## 常见错误

- 转换后残留TEMP自由度约束；先DDELE再ETCHG。
- 改变文件前缀后丢失rth来源；显式指定lesson23_th。
- 使用均匀温度却期待热弯曲；弯曲需要厚度梯度或差异膨胀。

## 练习

- 把上表面温度改为550/600/650 K，检查零梯度对照。
- 扩展多层燃料—包壳与界面导热，在POD误差中单独检查弯曲位移及层间应力。

## 命令依据

- [Ansys官方命令/单元参考](https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/ans_cmd/Hlp_C_ETCHG.html)
- [Ansys官方命令/单元参考](https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/ans_cmd/Hlp_C_LDREAD.html)

## 验证状态

Ansys MAPDL 2023 R1在本课validation隔离目录完成求解，返回码0、错误0。教学结果并非工程安全验证；尚未完成网格独立性及实测对照。

热结果温度范围550.0–650.0 K；Z位移范围-2.7489–0.0010 mm。结构子步收敛。存在1条ETCHG标准转换提醒，已核对转换为SOLID185、材料、温度传递和结构约束；未消除根部约束敏感性。