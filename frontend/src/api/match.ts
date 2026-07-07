/**
 * 智能匹配 API
 */
import request from './request'

export const matchApi = {
  /** 简历推荐职位 (求职者) - 匹配涉及 LLM 精排, 单独延长超时到 120s */
  recommendJobs: (resumeId: number, topK = 10) =>
    request.get(`/match/resume/${resumeId}/jobs`, { params: { top_k: topK }, timeout: 120000 }),
  /** 职位推荐候选人 (企业) */
  recommendResumes: (jobId: number, topK = 10) =>
    request.get(`/match/job/${jobId}/resumes`, { params: { top_k: topK }, timeout: 120000 }),
  /** 匹配历史 */
  history: (params: { page?: number; size?: number; direction?: string }) =>
    request.get('/match/history', { params }),
}
