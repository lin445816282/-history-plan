// 人物档案字段定义 —— 单一数据源，三种录入模式共用
// 严格对齐 db-schema.js 的 MODELS.profiles

export const FIELD_GROUPS = [
  {
    key: 'basic', label: '基础信息', core: true,
    fields: [
      { key: 'name', label: '人物名称', type: 'input', placeholder: '可自定义（本人/家人/模拟人物）' },
      { key: 'age', label: '当前年龄', type: 'input', placeholder: '如 28' },
      { key: 'era', label: '所处时代环境', type: 'textarea', placeholder: '当下外部大环境（经济、行业、社会环境）' },
      { key: 'region', label: '地域', type: 'input', placeholder: '生活工作地域' },
      { key: 'familyEconomicCapital', label: '家庭经济资本', type: 'textarea', placeholder: '家庭经济支持水平（宽裕/一般/紧张），具体描述' },
      { key: 'familyCulturalCapital', label: '家庭文化资本', type: 'textarea', placeholder: '家庭教育理念、可提供的文化资源（藏书、见识、指导）' },
      { key: 'familySymbolicCapital', label: '家庭符号资本', type: 'textarea', placeholder: '家庭在当地的社会声誉、关系网络' },
    ]
  },
  {
    key: 'self', label: '自身条件', core: true,
    fields: [
      { key: 'skills', label: '自身禀赋能力', type: 'textarea', placeholder: '掌握技能、优势能力' },
      { key: 'personality', label: '性格特质', type: 'textarea', placeholder: '性格优点、性格短板' },
      { key: 'mindset', label: '心性取舍', type: 'textarea', placeholder: '遇事倾向、执念、取舍习惯、心性弱点' },
      { key: 'health', label: '健康状况', type: 'textarea', placeholder: '身体、心理状态约束' },
    ]
  },
  {
    key: 'resources', label: '资源盘点', core: true,
    fields: [
      { key: 'financialResources', label: '资金储备', type: 'textarea', placeholder: '可支配资金、资产' },
      { key: 'networkResources', label: '人脉资源', type: 'textarea', placeholder: '可用人脉' },
      { key: 'timeResources', label: '时间资源', type: 'textarea', placeholder: '可支配时间' },
      { key: 'toolResources', label: '工具/技术资源', type: 'textarea', placeholder: '可使用的工具、技术条件' },
    ]
  },
  {
    key: 'goals', label: '约束与目标', core: true,
    fields: [
      { key: 'constraints', label: '现实约束困境风险', type: 'textarea', placeholder: '现实存在的难题、负债、限制' },
      { key: 'externalPressure', label: '外部压力', type: 'textarea', placeholder: '来自外部的压力' },
      { key: 'unchangeableLimits', label: '不可改变限制', type: 'textarea', placeholder: '客观无法突破的条件' },
      { key: 'shortTermGoal', label: '短期目标（0-1年）', type: 'textarea', placeholder: '短期想要达成事项' },
      { key: 'mediumTermGoal', label: '中期目标（1-3年）', type: 'textarea', placeholder: '中期想要达成事项' },
      { key: 'longTermGoal', label: '长期目标（3-10年）', type: 'textarea', placeholder: '长期愿景' },
    ]
  },
  {
    key: 'experience', label: '经历与变局', core: true,
    fields: [
      { key: 'keyDecisions', label: '过往经历关键抉择', type: 'textarea', placeholder: '过往重要选择、得失教训' },
      { key: 'externalChanges', label: '外部变局', type: 'textarea', placeholder: '非本人可控的突发环境变化' },
    ]
  },
  {
    key: 'extended', label: '扩展可选字段', core: false,
    fields: [
      { key: 'orgConstraints', label: '组织/团队约束', type: 'textarea', placeholder: '创业者、管理者适用' },
      { key: 'institutionalConstraints', label: '体制/规则环境约束', type: 'textarea', placeholder: '职场场景，单位制度、晋升天花板' },
      { key: 'cashFlow', label: '现金流/营收稳定性', type: 'textarea', placeholder: '个体、自由职业者适用' },
      { key: 'growthWindow', label: '关键成长窗口期', type: 'textarea', placeholder: '学生、家庭教育适用' },
      { key: 'externalExpectations', label: '外部期望', type: 'textarea', placeholder: '家庭、社会对本人的期待' },
      { key: 'legalRisks', label: '法律约束/合约风险', type: 'textarea', placeholder: '合约、债务、法律相关风险' },
      { key: 'networkStructure', label: '人脉强弱关系结构', type: 'textarea', placeholder: '强关系为主 / 弱关系为主 / 均衡' },
    ]
  },
]

// 全部字段（含扩展）
export const ALL_FIELDS = FIELD_GROUPS.flatMap(g => g.fields)

// 核心字段 key 列表
export const CORE_FIELD_KEYS = FIELD_GROUPS.filter(g => g.core).flatMap(g => g.fields.map(f => f.key))

// 扩展字段 key 列表
export const EXTENDED_FIELD_KEYS = FIELD_GROUPS.filter(g => !g.core).flatMap(g => g.fields.map(f => f.key))

// 字段 key → 字段定义
export const FIELD_MAP = Object.fromEntries(ALL_FIELDS.map(f => [f.key, f]))

// 极速建档 3 项必填：姓名 + 核心目标 + 当前最大困境
export const QUICK_REQUIRED = [
  { key: 'name', label: '① 人物名称', type: 'input', placeholder: '给自己/家人/模拟人物起个名字' },
  { key: 'shortTermGoal', label: '② 核心目标', type: 'textarea', placeholder: '你最想实现的一件事' },
  { key: 'constraints', label: '③ 当前最大困境', type: 'textarea', placeholder: '最困扰你的问题' },
]

// 对话式追问顺序（极速建档后逐步补全，跳过已填字段）
export const FOLLOWUP_ORDER = [
  'financialResources', 'networkResources', 'skills', 'personality',
  'mindset', 'health', 'era', 'region', 'age', 'timeResources',
  'toolResources', 'externalPressure', 'unchangeableLimits',
  'mediumTermGoal', 'longTermGoal', 'keyDecisions', 'externalChanges',
  'familyEconomicCapital', 'familyCulturalCapital', 'familySymbolicCapital',
]

// 空白档案模板
export function emptyProfile() {
  const p = { name: '' }
  ALL_FIELDS.forEach(f => { p[f.key] = '' })
  p.createdAt = ''
  p.updatedAt = ''
  return p
}

// 计算档案完整度（核心字段覆盖率，0-100）
export function completenessScore(profile) {
  const core = CORE_FIELD_KEYS
  const filled = core.filter(k => profile[k] && String(profile[k]).trim() !== '')
  return Math.round((filled.length / core.length) * 100)
}
