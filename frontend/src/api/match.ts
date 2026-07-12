/**
 * 智能匹配 API
 */
import request from './request'

export const matchApi = {
  /** 简历推荐职位 (求职者) - 匹配涉及 LLM 精排, 单独延长超时到 120s */
  recommendJobs: (resumeId: number, topK = 10) =>
    request.get(`/match/resume/${resumeId}/jobs`, { params: { top_k: topK }, timeout: 600000 }),
  /** 职位推荐候选人 (企业) */
  recommendResumes: (jobId: number, topK = 10) =>
    request.get(`/match/job/${jobId}/resumes`, { params: { top_k: topK }, timeout: 600000 }),
  /**
   * 获取简历与岗位的六维度匹配分 (统一匹配度数据源)
   * 匹配度主体是简历(resume), 入参 resume_id + job_id
   * 仅粗排规则计算, 无 LLM 调用, 响应 < 200ms
   */
  getScore: (resumeId: number, jobId: number) =>
    request.get('/match/score', { params: { resume_id: resumeId, job_id: jobId } }),
  /** 匹配历史 */
  history: (params: { page?: number; size?: number; direction?: string }) =>
    request.get('/match/history', { params }),
}
