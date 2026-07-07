/**
 * 消息 API
 */
import request from './request'

export const messageApi = {
  /** 发送消息 */
  send: (receiverId: number, content: string, jobId?: number) =>
    request.post('/messages', { receiver_id: receiverId, content, job_id: jobId }),
  /** 会话列表 */
  conversations: () => request.get('/messages/conversations'),
  /** 与某人的消息记录 */
  messagesWith: (userId: number) => request.get(`/messages/with/${userId}`),
  /** 标记已读 */
  markRead: (messageId: number) => request.post(`/messages/${messageId}/read`),
  /** 未读消息数 */
  unreadCount: () => request.get('/messages/unread-count'),
}
