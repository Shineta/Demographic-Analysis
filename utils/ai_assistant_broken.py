import streamlit as st
import openai
import os
from typing import Dict, List, Optional
import json

class AIAssistant:
    """AI Assistant for demographic analysis tool guidance and suggestions"""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def get_context_summary(self, data_available: bool = False, 
                           filters_applied: Dict = None, 
                           demographic_cols: List = None,
                           current_page: str = None,
                           analysis_results: Dict = None) -> str:
        """Generate comprehensive context summary for the AI assistant"""
        context = "User is working with a demographic analysis tool for educational content analysis. "
        
        if data_available:
            context += "Data is successfully loaded and validated. "
            if demographic_cols:
                context += f"Available demographics: {', '.join(demographic_cols[:5])}. "
            if filters_applied:
                active_filters = [f"{k}: {v}" for k, v in filters_applied.items() if v]
                if active_filters:
                    context += f"Active filters: {', '.join(active_filters)}. "
            if analysis_results:
                context += "Analysis has been completed with demographic gaps calculated. "
        else:
            context += "No data loaded yet - user needs to upload an Excel file. "
        
        if current_page:
            context += f"Currently viewing: {current_page}. "
            
        return context
    
    def get_ai_response(self, user_message: str, context: str) -> str:
        """Get AI response for user queries"""
        if not self.client:
            return self._get_fallback_response(user_message, context)
        
        try:
            system_prompt = f"""You are a helpful AI assistant for a demographic analysis tool used in educational content evaluation. 

            Current context: {context}

            Your role is to:
            1. Guide users through using the demographic analysis tool step-by-step
            2. Provide specific curriculum improvement suggestions based on demographic gaps
            3. Explain chart interpretations and data insights
            4. Help with feature navigation and troubleshooting
            5. Offer actionable recommendations for educational equity

            Guidelines:
            - Keep responses concise but comprehensive (150-250 words)
            - Focus on practical, actionable advice
            - When discussing demographic gaps, suggest specific content types
            - Reference current context and user's progress
            - Provide subject-specific recommendations (ELA, Science, Social Studies, Health)
            - Always maintain a supportive, educational tone
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return self._get_fallback_response(user_message, context)
    
    def _get_fallback_response(self, user_message: str, context: str) -> str:
        """Provide helpful responses when AI is unavailable"""
        user_lower = user_message.lower()
        
        # Guide responses based on keywords
        if any(word in user_lower for word in ['upload', 'file', 'data', 'start']):
            return """To get started:
1. Click "Browse files" to upload your Excel file
2. Ensure your file has columns for Grade, EntityDesc (modules), Component, TOTAL, and demographic data
3. Review the data preview to confirm proper formatting
4. The tool will automatically validate your data and show any issues"""

        elif any(word in user_lower for word in ['filter', 'target', 'demographic']):
            return """For analysis setup:
1. Use the sidebar to set demographic target percentages
2. Apply filters to focus on specific grades or components
3. The heat map will show gaps between actual and target representation
4. Red areas indicate under-representation, green shows over-representation"""

        elif any(word in user_lower for word in ['improve', 'curriculum', 'representation', 'gaps', 'suggestions']):
            return """To improve demographic representation:

**Immediate Actions:**
1. Identify modules with significant gaps (red areas in heat map)
2. Focus on largest gaps first for maximum impact
3. Review population heatmap to see grade-level patterns

**Content Strategies by Subject:**
• **ELA**: Add diverse authors, multicultural literature, varied perspectives
• **Social Studies**: Include underrepresented historical figures, global perspectives
• **Science**: Highlight scientists from diverse backgrounds, address historical exclusions
• **Health**: Ensure culturally responsive examples, diverse family structures

**Implementation:**
• Use the AI Curriculum Advisor for detailed subject recommendations
• Export comprehensive reports for content development teams
• Set realistic target percentages based on your student population
• Track progress over time with saved analysis sessions"""

        elif any(word in user_lower for word in ['export', 'report', 'download']):
            return """For exporting results:
1. Scroll to the bottom of the analysis section
2. Use the "Comprehensive Export" feature
3. Download includes: Excel reports, chart images, CSV data, and documentation
4. Perfect for presentations and sharing with curriculum teams"""

        elif any(word in user_lower for word in ['chart', 'visualization', 'heatmap']):
            return """Chart features:
1. Hover over heat map cells for detailed information
2. Use Population Distribution to see grade vs module patterns
3. Switch axes and change colors in the population heatmap
4. Module Population Analysis offers 5 different visualization types
5. All charts are interactive with detailed tooltips"""

        else:
            return """I'm here to help you navigate the demographic analysis tool! You can ask me about:
- Getting started with file uploads
- Setting up filters and targets
- Understanding the visualizations
- Improving curriculum representation
- Exporting reports and data

What specific aspect would you like help with?"""

def create_floating_assistant():
    """Create a simple AI assistant in sidebar"""
    # Initialize session state
    if 'assistant_messages' not in st.session_state:
        st.session_state.assistant_messages = []
    if 'show_assistant' not in st.session_state:
        st.session_state.show_assistant = False
    
    # Add to sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("🤖 AI Assistant", help="Get help with the tool"):
            st.session_state.show_assistant = not st.session_state.show_assistant
        
        if st.session_state.show_assistant:
            st.markdown("### AI Assistant")
            
            # Context detection
            data_available = st.session_state.get('data') is not None
            
            # Quick help buttons
            st.markdown("**Quick Help:**")
            
            if not data_available:
                if st.button("🚀 Getting Started", key="help_start"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "How do I get started?"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("How do I get started?", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                
                if st.button("📁 Upload Data", key="help_upload"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "How do I upload data?"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("How do I upload data?", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
            else:
                if st.button("📊 Understand Charts", key="help_charts"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "Help me understand the charts"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("Help me understand the charts", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                
                if st.button("💡 Improve Content", key="help_improve"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "How can I improve demographic representation?"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("How can I improve demographic representation?", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
            
            # Text input for questions
            user_input = st.text_input("Ask a question:", key="assistant_input", placeholder="How can I help you?")
            
            if user_input and user_input.strip():
                # Add user message
                st.session_state.assistant_messages.append({"role": "user", "content": user_input})
                
                # Get response
                assistant = AIAssistant()
                filters_applied = st.session_state.get('filters', {})
                demographic_cols = st.session_state.get('demographic_cols', [])
                context = assistant.get_context_summary(data_available, filters_applied, demographic_cols)
                response = assistant.get_ai_response(user_input, context)
                st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                
                # Limit history
                if len(st.session_state.assistant_messages) > 10:
                    st.session_state.assistant_messages = st.session_state.assistant_messages[-10:]
            
            # Show recent messages
            if st.session_state.assistant_messages:
                st.markdown("**Recent Chat:**")
                for message in st.session_state.assistant_messages[-4:]:  # Show last 4 messages
                    if message["role"] == "user":
                        st.markdown(f"**You:** {message['content']}")
                    else:
                        st.markdown(f"**Assistant:** {message['content']}")
                
                if st.button("Clear Chat", key="clear_chat"):
                    st.session_state.assistant_messages = []
                    st.rerun()
    

    
    # Toggle button
    if not st.session_state.assistant_visible:
        if st.button("🤖", key="toggle_assistant", help="Open AI Assistant"):
            st.session_state.assistant_visible = True
            st.rerun()
        
        st.markdown("""
        <div class="assistant-toggle" onclick="document.getElementById('toggle_assistant').click()">
            🤖
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Assistant interface
    with st.container():
        st.markdown('<div class="floating-assistant">', unsafe_allow_html=True)
        
        # Header
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown('<div class="assistant-header">🤖 AI Assistant</div>', unsafe_allow_html=True)
        with col2:
            if st.button("✕", key="close_assistant", help="Close Assistant"):
                st.session_state.assistant_visible = False
                st.rerun()
        
        # Chat container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        for i, message in enumerate(st.session_state.assistant_messages):
            if message['role'] == 'user':
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.assistant_messages = []
            st.rerun()
        
        # Input area
        user_input = st.text_input("Ask me anything about the tool...", key="assistant_input", placeholder="How do I upload data?")
        
        if user_input and user_input.strip():
            # Check if this is a duplicate message
            if (not st.session_state.assistant_messages or 
                st.session_state.assistant_messages[-1]["content"] != user_input):
                
                # Add user message
                st.session_state.assistant_messages.append({"role": "user", "content": user_input})
                
                # Get enhanced context
                data_available = st.session_state.get('data') is not None
                filters_applied = st.session_state.get('filters', {})
                demographic_cols = st.session_state.get('demographic_cols', [])
                analysis_results = st.session_state.get('analysis_results', {})
                
                # Determine current page context
                current_page = "Data Upload"
                if data_available:
                    if any(key.startswith('heatmap') for key in st.session_state.keys()):
                        current_page = "Heat Map Analysis"
                    elif any(key.startswith('pop_') for key in st.session_state.keys()):
                        current_page = "Population Analysis"
                    elif any(key.startswith('export') for key in st.session_state.keys()):
                        current_page = "Export Section"
                
                assistant = AIAssistant()
                context = assistant.get_context_summary(data_available, filters_applied, demographic_cols, current_page, analysis_results)
                
                # Get AI response
                response = assistant.get_ai_response(user_input, context)
                st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                
                # Keep only last 8 messages to avoid clutter
                if len(st.session_state.assistant_messages) > 8:
                    st.session_state.assistant_messages = st.session_state.assistant_messages[-8:]
                
                st.rerun()
        
        # Context-aware quick actions
        st.markdown("**Smart Help:**")
        
        # Dynamic buttons based on current state
        data_available = st.session_state.get('data') is not None
        
        if not data_available:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Get Started", key="get_started"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "How do I get started?"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("How do I get started?", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with col2:
                if st.button("📁 Upload Help", key="upload_help"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "How do I upload data?"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("How do I upload data?", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                    st.rerun()
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Interpret Charts", key="chart_help"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "Help me understand the charts"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("Help me understand the charts", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with col2:
                if st.button("💡 Improve Content", key="improve_help"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "How can I improve demographic representation?"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("How can I improve demographic representation?", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            
            col3, col4 = st.columns(2)
            with col3:
                if st.button("🎯 Set Targets", key="targets_help"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "How do I set demographic targets?"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("How do I set demographic targets?", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with col4:
                if st.button("📋 Export Reports", key="export_help"):
                    st.session_state.assistant_messages.append({"role": "user", "content": "How do I export my analysis?"})
                    assistant = AIAssistant()
                    response = assistant._get_fallback_response("How do I export my analysis?", "")
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)