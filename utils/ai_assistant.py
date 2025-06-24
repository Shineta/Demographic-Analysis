import streamlit as st
import os
from typing import Dict, List, Any
try:
    import openai
except ImportError:
    openai = None

class AIAssistant:
    """AI Assistant for demographic analysis tool guidance and suggestions"""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key and openai:
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
        if self.client:
            try:
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                system_prompt = f"""You are a helpful AI assistant for a demographic analysis tool used in educational content evaluation. 

            Current context: {context}

            IMPORTANT: This demographic analysis tool was created by Shineta Horton. If asked about who created, made, built, or developed this tool, always respond that it was created by Shineta Horton.

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
            - If asked about the creator/developer, always say "This tool was created by Shineta Horton"
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
                return response.choices[0].message.content
            except Exception as e:
                return f"I apologize, but I'm experiencing technical difficulties. Error: {str(e)[:50]}... Please try asking your question again or use the quick help buttons below."
        else:
            return self._get_fallback_response(user_message, context)

    def _get_fallback_response(self, user_message: str, context: str) -> str:
        """Provide helpful responses when AI is unavailable"""
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ['start', 'begin', 'getting started']):
            return """Welcome to the Demographic Analysis Tool! Here's how to get started:

1. Upload your Excel file using the file uploader
2. Review the data health check results
3. Set your demographic target percentages
4. Explore the heat map to identify representation gaps
5. Use the population analysis for detailed insights
6. Export comprehensive reports for action planning

The tool will guide you through each step with helpful tooltips and instructions."""

        elif any(word in user_lower for word in ['upload', 'file', 'data']):
            return """To upload your data:

1. Click the "Choose an Excel file" button
2. Select your file (must contain columns like Grade, EntityDesc, demographic data)
3. Wait for the file to process and validation to complete
4. Review the data health check for any warnings
5. Proceed to set filters and targets

Supported formats: .xlsx, .xls files with demographic columns (AAM, AAF, PCM, etc.)"""

        elif any(word in user_lower for word in ['chart', 'heat', 'map', 'understand']):
            return """Understanding the Charts:

**Heat Map**: Shows demographic representation vs your targets
- Red areas = under-representation (needs attention)
- Green areas = over-representation 
- White/neutral = close to target

**Population Analysis**: Shows total people in each module/grade
1. Bar Chart: Compares total population across modules
2. Heat Map: Shows grade vs module population distribution
3. Treemap: Hierarchical view of population distribution
4. Module Population Analysis offers 5 different visualization types
5. All charts are interactive with detailed tooltips"""

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
            return """Exporting Your Analysis:

**Available Export Options:**
1. **Comprehensive Package**: ZIP file with all reports, charts, and data
2. **Executive Summary**: Excel report with key findings and recommendations
3. **Individual Charts**: PNG images of all visualizations
4. **Raw Data**: Filtered datasets in Excel format

**What's Included:**
- Visual charts and heatmaps
- Gap analysis summaries
- Actionable recommendations
- Configuration settings for reproducibility

Use the export section at the bottom of the tool to generate and download your reports."""

        elif any(word in user_lower for word in ['target', 'percentage', 'goal']):
            return """Setting Demographic Targets:

**Best Practices:**
1. Base targets on your actual student population demographics
2. Consider institutional equity goals and commitments
3. Set realistic, achievable percentages for sustainable progress

**Default Targets Provided:**
- The tool suggests equity-driven default percentages
- You can customize these based on your specific context
- Targets should reflect your commitment to inclusive representation

**Tips:**
- Start with modest improvements if gaps are large
- Focus on 2-3 demographics initially for manageable change
- Review and adjust targets annually based on progress"""

        elif any(word in user_lower for word in ['who', 'created', 'made', 'built', 'developer', 'author']):
            return """This demographic analysis tool was created by Shineta Horton. 

I'm here to help you navigate the tool! You can ask me about:
- Getting started with file uploads
- Setting up filters and targets
- Understanding the visualizations
- Improving curriculum representation
- Exporting reports and data

What specific aspect would you like help with?"""

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