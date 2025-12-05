/**
 * 채팅 API 서비스
 * 백엔드 API와 통신하여 채팅 세션 생성 및 메시지 전송
 */

const API_URL = process.env.REACT_APP_API_URL || 'https://agent-backend-api-88199591627.us-east4.run.app';

// 토큰 저장 (메모리에 저장, 새로고침 시 초기화)
let accessToken = null;

/**
 * 토큰 설정
 */
export function setAccessToken(token) {
  accessToken = token;
}

/**
 * 토큰 가져오기
 */
export function getAccessToken() {
  return accessToken;
}

/**
 * 토큰 초기화
 */
export function clearAccessToken() {
  accessToken = null;
}

/**
 * 테스트용 JWT 토큰 생성
 * @param {string} userId - 사용자 ID
 * @returns {Promise<{access_token: string, user_id: string}>}
 */
export async function generateToken(userId) {
  try {
    const response = await fetch(`${API_URL}/auth/generate-token?user_id=${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to generate token: ${response.status}`);
    }

    const data = await response.json();
    // 토큰 저장
    setAccessToken(data.access_token);
    
    return {
      access_token: data.access_token,
      user_id: data.user_id,
    };
  } catch (error) {
    console.error('Error generating token:', error);
    throw error;
  }
}

/**
 * 새 채팅 세션 생성 (인증 필요)
 * @returns {Promise<{user_id: string, session_id: string}>}
 */
export async function createNewChat() {
  try {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    // 토큰이 있으면 Authorization 헤더 추가
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const response = await fetch(`${API_URL}/sessions/`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to create chat: ${response.status} ${response.statusText}`);
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
 * 메시지 전송 및 응답 수신 (인증 필요, 빈 응답 시 자동 재시도)
 * @param {string} userId - 사용자 ID
 * @param {string} sessionId - 세션 ID
 * @param {string} message - 전송할 메시지
 * @param {function} onChunk - 청크 수신 시 호출되는 콜백 (text: string)
 * @param {function} onDone - 완료 시 호출되는 콜백
 * @param {function} onError - 에러 발생 시 호출되는 콜백
 * @param {number} retryCount - 현재 재시도 횟수 (내부 사용)
 */
export async function sendMessage(userId, sessionId, message, onChunk, onDone, onError, retryCount = 0) {
  const MAX_RETRIES = 5;
  
  try {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    // 토큰이 있으면 Authorization 헤더 추가
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const response = await fetch(`${API_URL}/chat/message`, {
      method: 'POST',
      headers,
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
    
    // 빈 응답 체크 및 재시도
    if (!data.text || data.text.trim() === '') {
      if (retryCount < MAX_RETRIES) {
        console.log(`[ChatService] Empty response, retrying... (${retryCount + 1}/${MAX_RETRIES})`);
        // 잠시 대기 후 재시도
        await new Promise(resolve => setTimeout(resolve, 500));
        return sendMessage(userId, sessionId, message, onChunk, onDone, onError, retryCount + 1);
      } else {
        console.log(`[ChatService] Max retries reached, giving up.`);
        const fallbackText = '죄송합니다. 응답을 생성하는 데 문제가 발생했습니다. 다시 질문해주세요.';
        for (const char of fallbackText) {
          if (onChunk) onChunk(char);
        }
        if (onDone) onDone();
        return;
      }
    }
    
    // 정상 응답 처리
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
