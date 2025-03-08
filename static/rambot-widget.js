(function() {
    const fontAwesomeCss = document.createElement('link');
    fontAwesomeCss.rel = 'stylesheet';
    fontAwesomeCss.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css';
    fontAwesomeCss.integrity = 'sha512-Evv84Mr4kqVGRNSgIGL/F/aIDqQb7xQ2vcrdIwxfjThSH8CSR7PBEakCr51Ck+w+/U6swU2Im1vVX0SVk9ABhg==';
    fontAwesomeCss.crossOrigin = 'anonymous';
    fontAwesomeCss.referrerPolicy = 'no-referrer';
    document.head.appendChild(fontAwesomeCss);

    // API URL GOES HERE!
    const apiBaseUrlDev = '';

    function markdownToHTML(markdown) {
        return markdown
          .replace(/^##### (.*$)/gim, '<h5>$1</h5>') // H5
          .replace(/^#### (.*$)/gim, '<h4>$1</h4>')  // H4
          .replace(/^### (.*$)/gim, '<h3>$1</h3>')  // H3
          .replace(/^## (.*$)/gim, '<h2>$1</h2>')   // H2
          .replace(/^# (.*$)/gim, '<h1>$1</h1>')    // H1
          .replace(/\*\*(.*?)\*\*/gim, '<b>$1</b>') // Bold
          .replace(/\*(.*?)\*/gim, '<i>$1</i>')     // Italic
          .replace(/!\[(.*?)\]\((.*?)\)/gim, '<img alt="$1" src="$2" />') // Images
          .replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2">$1</a>') // Links
          .replace(/\n/g, '<br>'); // New lines
      }

    const handleFeedback = async function (isLike, messageId, event) {
        try {
            const session_id = localStorage.getItem('session_id');
            const response = await fetch(apiBaseUrlDev + '/api/v1/feedback', {
                method: 'PUT',
                headers: {
                'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                session_id: session_id,
                messageId: messageId,
                isLike: isLike
                })
            });

            if (!response.ok) {
                throw new Error('Failed to submit feedback');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
        } finally {
            const feedbackContainer = event.target.parentElement;
            feedbackContainer.innerText = 'Thank you for your feedback!';
            setTimeout(() => {
                feedbackContainer.innerText = '';
            }, 5000);
        }
    }

    const sendMessage = async function() {
        const input = document.querySelector('.chat-input');
        const text = input.value.trim();
        if (text) {
            createMessage(text, true);
            input.value = '';

            const messages = document.querySelector('.messages');
            const loader = document.createElement('div');
            loader.className = 'loader';
            messages.appendChild(loader);
            messages.scrollTop = messages.scrollHeight;

            try {
                const response = await fetch(apiBaseUrlDev + '/api/v1/chat', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_message: text })
                });
                const data = await response.json();
                const botResponse = markdownToHTML(data.response);
                localStorage.setItem('session_id', data.session_id);
                createMessage(botResponse, false, data.conversation_id);
            } catch (error) {
                console.error('Error:', error);
                createMessage('Sorry, there was an error processing your request.', false);
            } finally {
                loader.remove();
            }
        }
    }

    const resetSession = async function() {
        try {
            const response = await fetch(apiBaseUrlDev + '/clear_session', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        
            if (!response.ok) {
                throw new Error('Failed to reset session');
            }
            localStorage.removeItem('session_id');
            const messages = document.querySelector('.messages');
            messages.innerHTML = '';
        } catch (error) {
            console.error('Error resetting session:', error);
        }
    }

    const createMessage = function(text, isUser, conversationId) {
        const message = document.createElement('div');
        const messages = document.querySelector('.messages');
        message.className = `message ${isUser ? 'user' : 'bot'}`;

        if (conversationId) {
            message.dataset.conversationId = conversationId;
        }

        if (!isUser) {
            const avatar = document.createElement('div');
            avatar.className = 'avatar';
            message.appendChild(avatar);
        }

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.innerHTML = text;
        message.appendChild(bubble);

        if (!isUser) {
            const separator = document.createElement('hr');
            separator.className = 'feedback-separator';
            bubble.appendChild(separator);

            const feedbackQuestion = document.createElement('div');
            feedbackQuestion.className = 'feedback-question';
            feedbackQuestion.innerText = 'How was the response?';
            bubble.appendChild(feedbackQuestion);

            const feedback = document.createElement('div');
            feedback.className = 'feedback';
            const likeButton = document.createElement('button');
            likeButton.className = 'like-btn';
            likeButton.textContent = '👍';
            likeButton.addEventListener('click', (event) => handleFeedback(true, conversationId, event));
            feedback.appendChild(likeButton);

            const dislikeButton = document.createElement('button');
            dislikeButton.className = 'dislike-btn';
            dislikeButton.textContent = '👎';
            dislikeButton.addEventListener('click', (event) => handleFeedback(false, conversationId, event));
            feedback.appendChild(dislikeButton);

            bubble.appendChild(feedback);
        }
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    }

    window.createMessage = createMessage;
    window.handleFeedback = handleFeedback;
    window.sendMessage = sendMessage;
    window.resetSession = resetSession;

    const createWidget = () => {
        const container = document.createElement('div');
        container.id = 'widget-container';
        // Developed 2025 by an SF student! 
        container.innerHTML = `
            <div class="parent-chatbot-interface">
                <div class="chat-head">
                    <?xml version="1.0" encoding="UTF-8"?>
                    <svg id='Reward_Stars_3_24' width='24' height='24' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'><rect width='24' height='24' stroke='none' fill='#000000' opacity='0'/>
                    <g transform="matrix(0.84 0 0 0.84 12 12)" >
                    <path style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(255, 204, 35); fill-rule: evenodd; opacity: 1;" transform=" translate(-12.05, -12.12)" d="M 17.6602 1.1435 C 17.7466 0.813583 18.0447 0.583496 18.3858 0.583496 C 18.7268 0.583496 19.0249 0.813583 19.1113 1.1435 C 19.4417 2.40494 19.8041 3.17979 20.3464 3.7537 C 20.8915 4.3305 21.6901 4.78035 23.0512 5.23715 C 23.3567 5.33969 23.5625 5.62592 23.5625 5.94817 C 23.5625 6.27043 23.3567 6.55666 23.0512 6.65919 C 21.6901 7.116 20.8915 7.56584 20.3464 8.14265 C 19.8041 8.71656 19.4417 9.4914 19.1113 10.7529 C 19.0249 11.0828 18.7268 11.3128 18.3858 11.3128 C 18.0447 11.3128 17.7466 11.0828 17.6602 10.7529 C 17.3299 9.4914 16.9674 8.71656 16.4251 8.14265 C 15.8801 7.56584 15.0814 7.116 13.7204 6.65919 C 13.4149 6.55666 13.209 6.27043 13.209 5.94817 C 13.209 5.62592 13.4149 5.33969 13.7204 5.23715 C 15.0814 4.78035 15.8801 4.3305 16.4251 3.7537 C 16.9674 3.17979 17.3299 2.40494 17.6602 1.1435 Z M 8.05152 5.32096 C 8.13767 4.9907 8.43593 4.76025 8.77724 4.76025 C 9.11855 4.76025 9.41682 4.9907 9.50296 5.32096 C 10.0984 7.60394 10.7729 9.09454 11.8328 10.2207 C 12.8953 11.3496 14.4166 12.1882 16.8645 13.0131 C 17.1696 13.1159 17.375 13.4019 17.375 13.7238 C 17.375 14.0458 17.1696 14.3318 16.8645 14.4346 C 14.4166 15.2594 12.8953 16.0981 11.8328 17.2269 C 10.7729 18.3531 10.0984 19.8438 9.50296 22.1267 C 9.41682 22.457 9.11855 22.6874 8.77724 22.6874 C 8.43593 22.6874 8.13767 22.457 8.05152 22.1267 C 7.45604 19.8438 6.78163 18.3531 5.72165 17.2269 C 4.65922 16.0981 3.13784 15.2594 0.689949 14.4346 C 0.384882 14.3318 0.179443 14.0458 0.179443 13.7238 C 0.179443 13.4019 0.384882 13.1159 0.689949 13.0131 C 3.13784 12.1882 4.65922 11.3496 5.72165 10.2207 C 6.78163 9.09454 7.45604 7.60394 8.05152 5.32096 Z M 19.9017 15.4683 C 19.5621 15.4683 19.2649 15.6964 19.1771 16.0245 C 18.9366 16.9236 18.6804 17.4451 18.3143 17.8244 C 17.9439 18.2081 17.388 18.522 16.3909 18.8497 C 16.0831 18.9508 15.8751 19.2382 15.8751 19.5622 C 15.8751 19.8862 16.0831 20.1736 16.3909 20.2747 C 17.388 20.6023 17.9439 20.9163 18.3143 21.3 C 18.6804 21.6793 18.9366 22.2007 19.1771 23.0999 C 19.2649 23.428 19.5621 23.6561 19.9017 23.6561 C 20.2412 23.6561 20.5384 23.428 20.6262 23.0999 C 20.8667 22.2007 21.1229 21.6793 21.489 21.3 C 21.8594 20.9163 22.4153 20.6023 23.4124 20.2747 C 23.7202 20.1736 23.9283 19.8862 23.9283 19.5622 C 23.9283 19.2382 23.7202 18.9508 23.4124 18.8497 C 22.4153 18.522 21.8594 18.2081 21.489 17.8244 C 21.1229 17.4451 20.8667 16.9236 20.6262 16.0245 C 20.5384 15.6964 20.2412 15.4683 20.9017 15.4683 Z" stroke-linecap="round" />
                    </g>
                    </svg>
                </div>
                <div class="chat-container">
                    <div id="modal">
                        <h3>Send us your contact details!</h3>
                        <p>Would you like to receive updates from Asia Pacific College?</p>
                        <form id="lead-form">
                            <div class="input-wrapper">
                                <input type="text" name="name" class="chat-input" placeholder="Name" required>
                            </div>
                            <div class="input-wrapper">
                                <input type="email" name="email" class="chat-input" placeholder="Email" required>
                            </div>
                            <div class="input-wrapper">
                            <input type="tel" name="phone" class="chat-input" placeholder="Phone">
                            </div>
                            <div class="select-wrapper">
                                <label for="type">I am a...</label>
                                <select id="type" name="type" required>
                                    <option value="student">Student</option>
                                    <option value="applicant">Applicant</option>
                                    <option value="parent">Parent</option>
                                    <option value="staff">Staff</option>
                                    <option value="alumni">Alumni</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                            <button type="submit" class="submit-btn">Submit</button>
                            </form>
                            <button type="button" onclick="document.getElementById('modal').remove()" class="cancel-btn">No thanks, I just want to chat</button>
                    </div>
                    <div class="chat-header">
                    Chat with APC RamBot
                    <span class="pill">Experimental</span>
                    <button class="reset" onclick="resetSession()">Reset</button>
                    </div>
                    <div class="chat-info">
                    <div class="info-text">
                    RamBot is an experimental chatbot for Asia Pacific College developed by <a href="https://www.apc.edu.ph/programs/socit/">SoCIT</a> students. Powered by Azure OpenAI and Python.
                    </div>
                    <i class="fa fa-close"></i>
                    </div>
                    <div class="messages">
                        </div>
                        <div class="input-container">
                            <div class="input-wrapper">
                                <input type="text" id="chat-input" class="chat-input" placeholder="Type a message...">
                            </div>
                            <div class="send-button" onclick="sendMessage()">
                                <svg id='Send_Letter_24' width='24' height='24' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'><rect width='24' height='24' stroke='none' fill='#000000' opacity='0'/>


                                    <g transform="matrix(1 0 0 1 12 12)" >
                                    <path style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: currentColor; fill-rule: nonzero; opacity: 1;" transform=" translate(-12, -12)" d="M 12 2 C 6.486 2 2 6.486 2 12 C 2 17.514 6.486 22 12 22 C 17.514 22 22 17.514 22 12 C 22 6.486000000000001 17.514 2 12 2 z M 15.293 12.707 L 13 10.414 L 13 17 L 11 17 L 11 10.414 L 8.707 12.707 L 7.293000000000001 11.293000000000001 L 12 6.586 L 16.707 11.293 L 15.293 12.707 z" stroke-linecap="round" />
                                    </g>
                                    </svg>
                            </div>
                        </div>
                    <div class="disclaimer">RamBot might make mistakes. Verify important information. Contact <a href="mailto:admissions@apc.edu.ph">admissions</a> for official inquiries.</div>
                    </div>  
                </div>
            </div>
        `;

        const styles = document.createElement('style');
        styles.textContent = `
            @import url('https://fonts.googleapis.com/css2?family=Hind:wght@300;400;500;600;700&display=swap');

            *,
            *::before,
            *::after {
                box-sizing: border-box;
            }

            .loader {
            width: 60px;
            aspect-ratio: 2;
            --_g: no-repeat radial-gradient(circle closest-side,#35438c 90%,#0000);
            background: 
                var(--_g) 0%   50%,
                var(--_g) 50%  50%,
                var(--_g) 100% 50%;
            background-size: calc(100%/3) 50%;
            animation: l3 1s infinite linear;
            }

            @keyframes l3 {
                20%{background-position:0%   0%, 50%  50%,100%  50%}
                40%{background-position:0% 100%, 50%   0%,100%  50%}
                60%{background-position:0%  50%, 50% 100%,100%   0%}
                80%{background-position:0%  50%, 50%  50%,100% 100%}
            }

            .parent-chatbot-interface {
                font-family: 'Hind', sans-serif;
            }

            .chat-head {
                position: fixed;
                bottom: 5rem;
                right: 3rem;
                width: 60px;
                height: 60px;
                background: #35438c;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                z-index: 9999;
                transition: transform 0.2s ease;
            }

            .chat-head:hover {
                transform: scale(1.05);
            }

            .chat-head svg {
                width: 30px;
                height: 30px;
                margin: 15px;
            }

            .chat-container {
                position: fixed;
                right: -45vw;
                bottom: 150px;
                width: 30vw;
                height: 70vh;
                background: white;
                border-radius: 20px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                display: flex;
                flex-direction: column;
                transition: right 0.3s cubic-bezier(0.68, -0.55, 0.27, 1.55);
                z-index: 999;
            }

            .chat-container.active {
                right: 2rem;
            }

            .chat-header {
                padding: 10px 20px;
                background: #35438c;
                border-radius: 20px 20px 0 0;
                font-weight: 600;
                color: white;
            }

            .pill {
                background: #ffce47;
                color: #806715;
                padding: 4px 8px;
                border-radius: 20px;
                display: inline-block;
                margin: 0 5px;
                font-size: 0.8rem;
            }

            /* Media Query for Mobile */
            @media (max-width: 768px) {
                .chat-container {
                    width: 100vw;
                    height: 80vh;
                    right: -100vw;
                }

                .chat-container.active {
                    right: 0;
                }

                .chat-head {
                    bottom: 2rem;
                    right: 2rem;
                }

                #modal {
                    padding: 1rem;
                }

                #modal h3 {
                    font-size: 1.2rem;
                    margin-top: 0;
                }

                #modal p {
                    font-size: 0.9rem;
                }
            }

            @media (max-height: 800px) {
                #modal {
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                }
                
                #lead-form {
                    gap: 0.5rem; /* Reduce spacing between form elements */
                }
                
                .submit-btn {
                    margin-bottom: 0.5rem;
                }
            }

            @media (max-height: 600px) {
                #modal h3 {
                    margin-top: 0;
                    margin-bottom: 0.5rem;
                }
                
                #modal p {
                    margin-bottom: 0.5rem;
                }
            }

            /* Media Query for Smaller Screens */
            @media (max-width: 480px) {
                .chat-container {
                    height: 70vh;
                }

                .chat-head {
                    bottom: 1rem;
                    right: 1rem;
                }

                .chat-header {
                    font-size: 0.9rem;
                }
            }

            #modal {
                position: absolute;
                background: rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(12px);
                width: 100%;
                height: 100%;
                z-index: 999;
                border-radius: 20px;
                padding: 2rem;
                overflow-y: auto;
                color: white;
            }

            #lead-form {
                display: flex;
                flex-direction: column;
                gap: 1rem;
                margin: 0 auto;
            }

            .submit-btn {
                width: 100%;
                background: #35438c;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px;
                cursor: pointer;
                transition: background 0.3s;
                margin-bottom: 1rem;
            }

            select#type {
                width: 100%;
                padding: 12px 20px;
                border: 1px solid #ddd;
                border-radius: 10px;
                outline: none;
            }

            .submit-btn:hover {
                background: #4d69f1;
            }

            .cancel-btn {
                width: 100%;
                background:rgb(148, 144, 144);
                color: rgb(219, 219, 219);
                border: none;
                border-radius: 12px;
                padding: 12px;
                cursor: pointer;
                transition: background 0.3s;
            }

            .cancel-btn:hover {
                background:rgb(136, 135, 135);
            }

            .messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }

            .message {
                margin-bottom: 20px;
                display: flex;
                align-items: flex-start;
                gap: 10px;
            }

            .message.user {
                flex-direction: row-reverse;
            }

            .avatar {
                width: 30px;
                height: 30px;
                background-image: url('https://www.apc.edu.ph/wp-content/uploads/2019/05/Rams_Video_Still.png');
                background-size: cover;
                background-position: center;
                border-radius: 50%;
                flex-shrink: 0;
            }

            .bubble {
                padding: 12px 16px;
                border-radius: 18px;
                max-width: 70%;
                word-wrap: break-word;
            }

            .message.bot .bubble {
                background: white;
                border: 1px solid #e0e0e0;
            }

            .message.user .bubble {
                background: #d2d9ff;
            }

            .feedback-separator {
                border: 0;
                border-top: 1px solid #eee;
                margin: 5px 0;
                width: 80%;
                align-self: flex-start;
            }

            .feedback-question {
                font-size: 0.9em;
                color: #777;
                margin-bottom: 5px;
                align-self: flex-start;
            }

            .feedback button {
                background: none;
                border: none;
                cursor: pointer;
                padding: 5px;
            }

            .feedback button:hover {
                background: #f5f5f5;
                border-radius: 50%;
            }

            .send-button {
                background: none;
                margin-left: 8px;
                color: rgb(46, 46, 46);
                border: none;
                border-radius: 12px;
                cursor: pointer;
                transition: background 0.3s;
                font-family: inherit;
            }

            .send-button svg {
                width: 35px;
                height: 35px;
                color: #35438c;
                transition: color 0.15s;
            }

            .send-button:hover svg {
                color: #4d69f1;
            }

            .input-container {
                padding: 20px;
                border-top: 1px solid #eee;
                display: flex;
                align-items: center;
            }

            .input-wrapper {
                position: relative;
                flex-grow: 1;
            }

            .input-wrapper::before {
                content: '';
                position: absolute;
                inset: -3px;
                border-radius: 12px;
                background: linear-gradient(45deg, #596fff, #1e3cff);
                opacity: 0;
                transition: opacity 0.3s;
                z-index: -1;
            }

            .input-wrapper:focus-within::before {
                opacity: 1;
            }

            .chat-input {
                width: 100%;
                padding: 12px 20px;
                border: 1px solid #ddd;
                border-radius: 10px;
                outline: none;
                background: white;
            }

            .reset {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 0.8em;
                padding: 4px 8px;
                border-radius: 20px;
                transition: background 0.3s;
                float: right;
            }

            .reset:hover {
                background: rgba(255, 255, 255, 0.1);
            }

            .disclaimer {
                font-size: 0.75em;
                color: #666;
                text-align: center;
                margin-bottom: 16px;
            }

            .chat-info {
                padding: 20px;
                background: #f5f5f5;
                font-size: 0.8em;
                text-align: center;
                color: #666;
                display: flex;
                justify-content: space-between;
            }

            .chat-info i {
                cursor: pointer;
                font-size: 1.5em;
            }

            .feedback-thankyou {
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }
        `;

        const initWidget = () => {
            const chatHead = document.querySelector('.chat-head');
            const chatContainer = document.querySelector('.chat-container');
            const input = document.querySelector('#chat-input');
            const messages = document.querySelector('.messages');
            const leadForm = container.querySelector('#lead-form');
            const closeInfoBtn = document.querySelector('.chat-info i');
            const chatInfo = document.querySelector('.chat-info');

            if (closeInfoBtn && chatInfo) {
                closeInfoBtn.addEventListener('click', () => {
                    chatInfo.style.display = 'none';
                    localStorage.setItem('chatInfoClosed', 'true');
                });
            }

            if (localStorage.getItem('chatInfoClosed')) {
                chatInfo.style.display = 'none';
            }

            chatHead.addEventListener('click', () => {
                chatContainer.classList.toggle('active');
            });
        
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });

            leadForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const formData = new FormData(event.target);
                const data = Object.fromEntries(formData.entries());
    
                try {
                    const response = await fetch(apiBaseUrlDev + '/api/v1/lead', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    });
    
                    if (!response.ok) {
                        throw new Error('Failed to submit lead');
                    }
    
                    const modal = document.getElementById('modal');
                    modal.remove();
                } catch (error) {
                    console.error('Error submitting lead:', error);
                }
            });
        };

        document.body.appendChild(container);
        document.head.appendChild(styles);

        initWidget();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
    } else {
        createWidget();
    }
})();
