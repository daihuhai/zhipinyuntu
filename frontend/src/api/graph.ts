/**
 * 知识图谱 API
 */
import request from './request'

export const graphApi = {
  /** 简历能力图谱 */
  resumeGraph: (resumeId: number) => request.get(`/graph/resume/${resumeId}`),
  /** 技能关联图谱 */
  skillGraph: (skillName: string) => request.get(`/graph/skill/${skillName}`),
}
