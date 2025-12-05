import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { createNewChat, sendMessage, generateToken, getAccessToken, clearAccessToken } from './services/chatService';

const AgentChat = () => {
  const [inputValue, setInputValue] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [userId, setUserId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [textareaHeight, setTextareaHeight] = useState(50);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  
  // 로그인 상태
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginUserId, setLoginUserId] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  
  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const isAtBottomRef = useRef(true);
  
  // 스트리밍용 refs
  const pendingTextRef = useRef('');
  const pendingBotIdRef = useRef(null);
  const chunkQueueRef = useRef([]);
  const isProcessingRef = useRef(false);

  const recommendedQuestions = [
    '소프트웨어 과목 찾아줘',
    '경영학과 졸업 하려면 어떻게 해야해??',
    '교수님 이메일이 뭐야??',
  ];

  // 로그인 처리
  const handleLogin = async (e) => {
    e.preventDefault();
    if (!loginUserId.trim() || isLoggingIn) return;
    
    setIsLoggingIn(true);
    setLoginError('');
    
    try {
      const { user_id } = await generateToken(loginUserId.trim());
      console.log('Token generated for user:', user_id);
      setIsLoggedIn(true);
      // 로그인 후 자동으로 세션 시작
      startNewSession();
    } catch (error) {
      console.error('Login failed:', error);
      setLoginError('로그인에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // 로그아웃 처리
  const handleLogout = () => {
    clearAccessToken();
    setIsLoggedIn(false);
    setUserId(null);
    setSessionId(null);
    setChatMessages([]);
    setLoginUserId('');
  };

  // 세션 시작 함수 (재사용 가능)
  const startNewSession = async () => {
    if (!getAccessToken()) {
      setChatMessages([{
        text: '로그인이 필요합니다.',
        sender: 'bot'
      }]);
      return;
    }
    
    try {
      const { user_id, session_id } = await createNewChat();
      setUserId(user_id);
      setSessionId(session_id);
      setChatMessages([]); // 채팅 내역 초기화
    } catch (error) {
      console.error('Failed to create chat:', error);
      setChatMessages([{
        text: '죄송합니다. 채팅 세션을 시작할 수 없습니다. 잠시 후 다시 시도해주세요.',
        sender: 'bot'
      }]);
    }
  };

  // 모바일 감지
  useEffect(() => {
    const checkMobile = () => {
      const userAgent = navigator.userAgent || navigator.vendor || window.opera;
      const isMobileDevice = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase());
      const isSmallScreen = window.innerWidth < 768;
      setIsMobile(isMobileDevice || isSmallScreen);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);

    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);

  // 직접 렌더링
  const updateBotMessage = (text, botId, isStreaming = true) => {
    setChatMessages(prev => {
      const idx = prev.map(m => m.id).lastIndexOf(botId);
      if (idx === -1) return prev;
      
      const next = [...prev];
      next[idx] = { ...next[idx], text, isStreaming, isTyping: false };
      return next;
    });
  };

  // 청크 큐 프로세서 - 타자기 효과
  const processChunkQueue = () => {
    if (isProcessingRef.current || chunkQueueRef.current.length === 0) {
      return;
    }
    
    isProcessingRef.current = true;
    
    const processNext = () => {
      if (chunkQueueRef.current.length === 0) {
        isProcessingRef.current = false;
        return;
      }
      
      const chunk = chunkQueueRef.current.shift();
      pendingTextRef.current += chunk;
      
      updateBotMessage(pendingTextRef.current, pendingBotIdRef.current, true);
      
      setTimeout(processNext, 10);
    };
    
    processNext();
  };

  // 스크롤이 맨 아래에 있는지 확인
  const checkIfAtBottom = () => {
    if (!chatContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const threshold = 50;
    return scrollHeight - scrollTop - clientHeight < threshold;
  };

  // 맨 아래로 스크롤
  const scrollToBottom = (behavior = 'smooth') => {
    if (chatContainerRef.current) {
      requestAnimationFrame(() => {
        if (chatContainerRef.current) {
          chatContainerRef.current.scrollTo({
            top: chatContainerRef.current.scrollHeight,
            behavior: behavior
          });
          isAtBottomRef.current = true;
          setShowScrollButton(false);
        }
      });
    }
  };

  // 스크롤 이벤트 핸들러
  const handleScroll = () => {
    const isAtBottom = checkIfAtBottom();
    isAtBottomRef.current = isAtBottom;
    setShowScrollButton(!isAtBottom);
  };

  // 새 메시지 도착 시 자동 스크롤 (맨 아래에 있을 때만)
  useEffect(() => {
    if (chatMessages.length > 0 && isAtBottomRef.current) {
      const behavior = 'auto';
      scrollToBottom(behavior);
    }
  }, [chatMessages]);


  const handleSendMessage = async () => {
    if (inputValue.trim() === '' || !userId || !sessionId || isLoading) return;

    const messageText = inputValue.trim();
    const userMessage = { text: messageText, sender: 'user', id: Date.now() };
    const botMessageId = Date.now() + 1;

    const typingIndicator = {
       text: '',
       sender: 'bot',
       id: botMessageId,
       isTyping: true
     };
    
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.value = '';
      textareaRef.current.style.height = '50px';
      setTextareaHeight(50);
    }
    
    setChatMessages(prev => [...prev, userMessage, typingIndicator]);
    isAtBottomRef.current = true;
    setIsLoading(true);
    
    pendingBotIdRef.current = botMessageId;
    pendingTextRef.current = '';

    try {
      await sendMessage(
        userId,
        sessionId,
        messageText,
        (chunk) => {
          chunkQueueRef.current.push(chunk);
          
          if (!isProcessingRef.current) {
            processChunkQueue();
          }
        },
        () => {
          const waitForQueue = () => {
            if (chunkQueueRef.current.length > 0 || isProcessingRef.current) {
              setTimeout(waitForQueue, 50);
              return;
            }
            
            const botId = pendingBotIdRef.current;
            setIsLoading(false);
            updateBotMessage(pendingTextRef.current, botId, false);
            
            pendingBotIdRef.current = null;
            pendingTextRef.current = '';
            chunkQueueRef.current = [];
          };
          
          waitForQueue();
        },
        (errorMessage) => {
          const botId = pendingBotIdRef.current;
          setIsLoading(false);
          
          updateBotMessage(`죄송합니다. 오류가 발생했습니다: ${errorMessage}`, botId, false);
          
          pendingBotIdRef.current = null;
          pendingTextRef.current = '';
        }
      );
    } catch (error) {
      console.error('Error sending message:', error);
      
      const botId = pendingBotIdRef.current;
      setIsLoading(false);
      
      updateBotMessage('죄송합니다. 메시지 전송에 실패했습니다. 다시 시도해주세요.', botId, false);
      
      pendingBotIdRef.current = null;
      pendingTextRef.current = '';
    }
  };

  const handleRecommendationClick = async (question) => {
    if (!userId || !sessionId || isLoading) return;

    const userMessage = { text: question, sender: 'user', id: Date.now() };
    const botMessageId = Date.now() + 1;
    
    const typingIndicator = {
       text: '',
       sender: 'bot',
       id: botMessageId,
       isTyping: true
     };

    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.value = '';
      textareaRef.current.style.height = '50px';
      setTextareaHeight(50);
    }

    setChatMessages(prev => [...prev, userMessage, typingIndicator]);
    isAtBottomRef.current = true;
    setIsLoading(true);
    
    pendingBotIdRef.current = botMessageId;
    pendingTextRef.current = '';

    try {
      await sendMessage(
        userId,
        sessionId,
        question,
        (chunk) => {
          chunkQueueRef.current.push(chunk);
          
          if (!isProcessingRef.current) {
            processChunkQueue();
          }
        },
        () => {
          const waitForQueue = () => {
            if (chunkQueueRef.current.length > 0 || isProcessingRef.current) {
              setTimeout(waitForQueue, 50);
              return;
            }
            
            const botId = pendingBotIdRef.current;
            setIsLoading(false);
            updateBotMessage(pendingTextRef.current, botId, false);
            
            pendingBotIdRef.current = null;
            pendingTextRef.current = '';
            chunkQueueRef.current = [];
          };
          
          waitForQueue();
        },
        (errorMessage) => {
          const botId = pendingBotIdRef.current;
          setIsLoading(false);
          
          updateBotMessage(`죄송합니다. 오류가 발생했습니다: ${errorMessage}`, botId, false);
          
          pendingBotIdRef.current = null;
          pendingTextRef.current = '';
        }
      );
    } catch (error) {
      console.error('Error sending message:', error);
      
      const botId = pendingBotIdRef.current;
      setIsLoading(false);
      
      updateBotMessage('죄송합니다. 메시지 전송에 실패했습니다. 다시 시도해주세요.', botId, false);
      
      pendingBotIdRef.current = null;
      pendingTextRef.current = '';
    }
  };


  // textarea 높이 자동 조절
  const adjustTextareaHeight = (textarea) => {
    if (textarea) {
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;

      const minHeight = 50;
      const maxHeight = 120;
      const newHeight = Math.max(minHeight, Math.min(scrollHeight, maxHeight));
      
      textarea.style.height = newHeight + 'px';
      setTextareaHeight(newHeight);
    }
  };

  const handleTextareaChange = (e) => {
    setInputValue(e.target.value);
    adjustTextareaHeight(e.target);
  };

  // 로그인 화면
  if (!isLoggedIn) {
    return (
      <div 
        className="flex flex-col w-full overflow-hidden bg-gradient-to-br from-sky-100 to-sky-200 dark:from-sky-800 dark:to-sky-900 font-display text-gray-800 dark:text-gray-200"
        style={{ height: '100dvh' }}
      >
        <div className="flex flex-col items-center justify-center flex-1 p-6">
          <div className="w-full max-w-md bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-2xl shadow-xl p-8">
            <h1 className="text-3xl font-bold text-center text-gray-800 dark:text-white mb-2">
              🌽 강냉이
            </h1>
            <p className="text-center text-gray-600 dark:text-gray-400 mb-8">
              강남대학교 AI 챗봇
            </p>
            
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label 
                  htmlFor="userId" 
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  사용자 번호 입력
                </label>
                <input
                  type="text"
                  id="userId"
                  value={loginUserId}
                  onChange={(e) => setLoginUserId(e.target.value)}
                  placeholder="예: 1, 2, 3..."
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                  disabled={isLoggingIn}
                />
                <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  ⚠️ 테스트용 로그인입니다. 아무 숫자나 입력하세요.
                </p>
              </div>
              
              {loginError && (
                <p className="text-red-500 text-sm text-center">{loginError}</p>
              )}
              
              <button
                type="submit"
                disabled={!loginUserId.trim() || isLoggingIn}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors shadow-lg"
              >
                {isLoggingIn ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⏳</span>
                    로그인 중...
                  </span>
                ) : (
                  '시작하기'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // 채팅 화면
  return (
    <div 
      className="flex flex-col w-full overflow-hidden bg-gradient-to-br from-sky-100 to-sky-200 dark:from-sky-800 dark:to-sky-900 font-display text-gray-800 dark:text-gray-200"
      style={{ height: '100dvh' }}
    >
      <div className="flex flex-col items-center p-2 md:p-6 lg:p-6 flex-1 min-h-0">
        {/* 헤더 */}
        <div className="flex items-center justify-between w-full max-w-2xl mb-4 flex-shrink-0">
          <button
            onClick={startNewSession}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-white/50 dark:bg-black/20 backdrop-blur-sm border border-white/60 dark:border-white/20 rounded-lg hover:bg-white/70 dark:hover:bg-black/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-xl">+</span>
            <span className="font-medium">New</span>
          </button>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">강남대학교 챗봇</h1>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1 px-3 py-2 text-sm bg-white/50 dark:bg-black/20 backdrop-blur-sm border border-white/60 dark:border-white/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
          >
            <span>🚪</span>
            <span>로그아웃</span>
          </button>
        </div>

        {chatMessages.length === 0 ? (
          // Initial View
          <div className="flex w-full max-w-2xl flex-col items-center justify-center gap-6 flex-1 min-h-0 py-4 overflow-hidden">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800 dark:text-white">강남대학교 챗봇 강냉이</h1>
            <div className="w-full px-4">
              <div className="flex flex-wrap justify-center gap-3">
                {recommendedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleRecommendationClick(question)}
                    className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-full h-10 px-4 bg-white/50 dark:bg-black/20 backdrop-blur-sm border border-white/60 dark:border-white/20 text-gray-700 dark:text-gray-200 text-sm font-medium hover:bg-white/70 dark:hover:bg-black/30 transition-colors"
                  >
                    <span className="truncate">{question}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Chat View
          <div 
            className={`w-full max-w-2xl flex-1 flex flex-col min-h-0 ${isMobile ? '' : 'mb-3'}`}
            style={!isMobile ? {
              maxHeight: `calc(100vh - ${textareaHeight + 120}px)`,
              minHeight: '700px',
              transition: 'max-height 0.2s ease-out'
            } : undefined}
          >
            <div
              ref={chatContainerRef}
              onScroll={handleScroll}
              className={`w-full chat-container bg-gradient-to-b from-sky-50 to-sky-100 rounded-lg px-4 pt-2 flex-1 min-h-0 overflow-y-auto ${
                isMobile ? 'pb-24' : 'pb-1'
              }`}
              style={{
                scrollBehavior: 'smooth',
                backgroundAttachment: 'local',
                contain: 'layout style'
              }}
            >
            {chatMessages.map((message, index) => (
              <div key={message.id ?? index} className={`flex my-1.5 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`rounded-lg px-4 py-2 max-w-lg chat-message shadow-sm ${message.sender === 'user' ? 'user-message bg-blue-600 text-white shadow-sm rounded-2xl' : 'bot-message bg-white/90 text-gray-800 border border-gray-200 shadow-sm rounded-2xl backdrop-blur-sm'}`}
                  style={{
                    willChange: 'transform',
                    backgroundAttachment: 'scroll'
                  }}
                >
                  {message.sender === 'bot' ? (
                     message.isTyping ? (
                         <div className="typing-dots">
                           <div></div><div></div><div></div>
                         </div>
                    ) :
                    message.isStreaming ? (
                      <div className="whitespace-pre-wrap animate-fade-in">{message.text}</div>
                    ) : (
                      <div className="markdown-body animate-fade-in">
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                            ul: ({node, ...props}) => <ul className="list-disc ml-4 mb-2" {...props} />,
                            ol: ({node, ...props}) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                            li: ({node, ...props}) => <li className="mb-1" {...props} />,
                            strong: ({node, ...props}) => <strong className="font-bold" {...props} />,
                            em: ({node, ...props}) => <em className="italic" {...props} />,
                            a: ({node, children, href, ...props}) => (
                              <a
                                className="text-blue-600 underline hover:text-blue-800"
                                target="_blank"
                                rel="noopener noreferrer"
                                href={href}
                                {...props}
                              >
                                {children || href}
                              </a>
                            ),
                            code: ({node, inline, ...props}) => 
                              inline ? 
                                <code className="bg-gray-300 px-1 rounded text-sm" {...props} /> :
                                <code className="block bg-gray-300 p-2 rounded text-sm overflow-x-auto" {...props} />
                          }}
                        >
                          {message.text}
                        </ReactMarkdown>
                      </div>
                    )
                  ) : (
                    message.text
                  )}
                </div>
              </div>
            ))}
            
            {/* 맨 아래로 스크롤 버튼 */}
            {showScrollButton && (
              <div className="sticky bottom-0 left-0 right-0 flex justify-center py-3 pointer-events-none">
                <button
                  onClick={() => scrollToBottom('smooth')}
                  className="flex items-center justify-center w-10 h-10 rounded-full bg-white dark:bg-gray-800 shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200 dark:border-gray-700 hover:scale-110 pointer-events-auto"
                  aria-label="맨 아래로 스크롤"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2.5}
                    stroke="currentColor"
                    className="w-5 h-5 text-gray-700 dark:text-gray-300"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M19.5 13.5L12 21m0 0l-7.5-7.5M12 21V3"
                    />
                  </svg>
                </button>
              </div>
            )}
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className={`w-full flex justify-center ${
        isMobile 
          ? 'sticky bottom-0 bg-white/70 dark:bg-gray-900/70 backdrop-blur-md border-t border-white/40 dark:border-gray-700 pt-2' 
          : 'px-2 md:px-6 lg:px-6 pb-3'
      }`}
      style={isMobile ? { paddingBottom: 'calc(var(--safe-bottom) + 8px)' } : undefined}
      >
        <div className="w-full max-w-2xl">
          <div className="relative flex items-start">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={handleTextareaChange}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  if (e.nativeEvent.isComposing) {
                    return;
                  }
                  
                  if (e.metaKey || e.ctrlKey) {
                    e.preventDefault();
                    
                    const textarea = e.target;
                    const start = textarea.selectionStart;
                    const end = textarea.selectionEnd;
                    const newValue = inputValue.substring(0, start) + '\n' + inputValue.substring(end);
                    
                    setInputValue(newValue);
                    
                    requestAnimationFrame(() => {
                      textarea.selectionStart = textarea.selectionEnd = start + 1;
                      adjustTextareaHeight(textarea);
                    });
                    return;
                  } else if (!e.shiftKey) {
                    e.preventDefault();
                    
                    if (inputValue.trim() === '') {
                      return;
                    }
                    
                    handleSendMessage();
                  }
                }
              }}
              className="w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white py-3 pl-5 pr-14 text-base focus:ring-2 focus:ring-[#4682B4] focus:border-[#4682B4] transition-shadow shadow-lg resize-none max-h-[120px] leading-relaxed"
              placeholder="강냉이에게 무엇이든 물어보세요..."
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="absolute right-3 bottom-2 flex h-9 w-9 items-center justify-center
                  + rounded-full bg-white/40 dark:bg-white/20 backdrop-blur-md
                  + text-gray-700 hover:bg-white/60 dark:hover:bg-white/30
                  + transition-all disabled:opacity-40 disabled:cursor-not-allowed">
              {isLoading ? (
                    <span className="animate-pulse text-gray-500">•••</span>
                  ) : (
                    <span className="material-symbols-outlined text-gray-700 dark:text-gray-200">send</span>
                  )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentChat;
