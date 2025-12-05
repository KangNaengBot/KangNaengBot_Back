/**
 * 채팅 API 서비스
 * 백엔드 API와 통신하여 채팅 세션 생성 및 메시지 전송
 */

const API_URL = process.env.REACT_APP_API_URL || 'https://agent-backend-api-88199591627.us-east4.run.app';

/**
 * 새 채팅 세션 생성
 * @returns {Promise<{user_id: string, session_id: string}>}
 */
export async function createNewChat() {
  try {
    const response = await fetch(`${API_URL}/sessions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to create chat: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return {
      user_id: data.user_id,
      session_id: data.session_id,
    };
  } catch (error) {
    console.error('Error creating new chat:', error);
    throw error;
  }
}

/**
 * 메시지 전송 및 응답 수신
 * @param {string} userId - 사용자 ID
 * @param {string} sessionId - 세션 ID
 * @param {string} message - 전송할 메시지
 * @param {function} onChunk - 청크 수신 시 호출되는 콜백 (text: string)
 * @param {function} onDone - 완료 시 호출되는 콜백
 * @param {function} onError - 에러 발생 시 호출되는 콜백
 */
export async function sendMessage(userId, sessionId, message, onChunk, onDone, onError) {
  try {
    const response = await fetch(`${API_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionId,
        message: message,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to send message: ${response.status} ${response.statusText}`);
    }

    // JSON 응답 처리
    const data = await response.json();
    
    if (data.text) {
      // 타자기 효과를 위해 문자 단위로 청크 전달
      for (const char of data.text) {
        if (onChunk) onChunk(char);
      }
    }
    
    if (onDone) onDone();
    
  } catch (error) {
    console.error('Error in sendMessage:', error);
    if (onError) {
      onError(error.message || 'Failed to send message');
    }
    throw error;
  }
}
