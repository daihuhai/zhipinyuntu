/**
 * 面试相关 API
 */
import request from './request'

export const interviewApi = {
  /** 灵犀AI生成面试问题 (根据候选人简历+职位要求) */
  generateQuestions: (applicationId: number) =>
    request.post('/interviews/generate-questions', { application_id: applicationId }, { timeout: 600000 }),
}
