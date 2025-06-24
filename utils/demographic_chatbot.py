import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import streamlit as st
from openai import OpenAI
import os
import json

class DemographicChatbot:
    """AI-powered chatbot for demographic balancing recommendations"""
    
    def __init__(self):
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        if self.openai_key:
            self.client = OpenAI(api_key=self.openai_key)
            self.available = True
        else:
            self.available = False
    
    def analyze_demographic_gaps(self, df: pd.DataFrame, demographic_cols: List[str], 
                                targets: Dict[str, float]) -> Dict[str, Any]:
        """Analyze current demographic representation vs targets"""
        
        total_people = df['TOTAL'].sum()
        analysis = {
            'total_people': total_people,
            'demographics': {},
            'gaps': {},
            'recommendations_needed': []
        }
        
        for demo_col in demographic_cols:
            if demo_col in df.columns:
                actual_count = df[demo_col].sum()
                actual_pct = (actual_count / total_people) * 100
                target_pct = targets.get(demo_col.lower(), targets.get(demo_col, 10))
                gap = actual_pct - target_pct
                
                analysis['demographics'][demo_col] = {
                    'actual_count': int(actual_count),
                    'actual_percentage': round(actual_pct, 1),
                    'target_percentage': target_pct,
                    'gap': round(gap, 1),
                    'gap_count': int((gap / 100) * total_people)
                }
                
                if abs(gap) > 2:  # Significant gap
                    analysis['recommendations_needed'].append(demo_col)
        
        return analysis
    
    def generate_balancing_suggestions(self, analysis: Dict[str, Any], 
                                     module_name: str = "Overall Dataset") -> str:
        """Generate AI-powered suggestions for demographic balancing"""
        
        if not self.available:
            return self._generate_fallback_suggestions(analysis, module_name)
        
        try:
            # Prepare data for AI analysis
            prompt = self._create_analysis_prompt(analysis, module_name)
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an education equity assistant helping align K-8 curriculum modules with demographic representation goals. Focus only on instructional content (lessons, texts, visuals, characters, stories, themes), not staffing or HR-related topics. Provide specific curriculum-level content updates to better reflect underrepresented demographic groups."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return self._format_ai_response(result)
            
        except Exception as e:
            st.error(f"AI analysis temporarily unavailable: {e}")
            return self._generate_fallback_suggestions(analysis, module_name)
    
    def _create_analysis_prompt(self, analysis: Dict[str, Any], module_name: str) -> str:
        """Create detailed prompt for AI analysis"""
        
        demographics_text = ""
        for demo, data in analysis['demographics'].items():
            demographics_text += f"\n- {demo}: {data['actual_percentage']}% (target: {data['target_percentage']}%, gap: {data['gap']:+.1f}%)"
        
        prompt = f"""
        You are analyzing demographic representation within K-8 educational curriculum modules for {module_name}.
        
        Total People Represented in Content: {analysis['total_people']:,}
        
        Current Demographics in Educational Content:{demographics_text}
        
        Based on this data, identify which curriculum modules are underrepresenting key demographic groups.
        
        Please provide a JSON response with:
        1. "content_updates": List of 3-5 specific curriculum content changes (revising characters, story settings, themes, illustrations, vocabulary examples)
        2. "module_recommendations": Specific suggestions for updating instructional materials to better represent underrepresented demographics
        3. "implementation_timeline": Realistic timeframe for content revisions
        4. "content_considerations": Potential challenges in curriculum updates
        5. "progress_metrics": How to measure improved representation in educational materials
        
        Focus only on instructional content changes. Avoid HR-style language about hiring, recruiting, outreach, or employee training.
        This analysis applies strictly to curriculum materials, lessons, and educational content.
        """
        
        return prompt
    
    def _format_ai_response(self, ai_result: Dict[str, Any]) -> str:
        """Format AI response into readable recommendations with enhanced formatting"""
        
        formatted = "## Curriculum Representation Recommendations\n\n"
        
        # Add summary section
        if "content_updates" in ai_result and ai_result["content_updates"]:
            formatted += "### Summary of Recommendations\n"
            formatted += f"- **Total Suggested Changes:** {len(ai_result['content_updates'])}\n"
            formatted += "- **Focus Areas:** ELA, Social Studies, Science, Health Education\n"
            formatted += "- **Implementation Approach:** Gradual content updates over 6-12 months\n\n"
        
        if "content_updates" in ai_result:
            formatted += "### Priority Content Updates\n"
            
            # Group recommendations by subject area
            ela_recs = []
            social_studies_recs = []
            science_recs = []
            health_recs = []
            general_recs = []
            
            for action in ai_result["content_updates"]:
                # Handle both string and dict formats
                if isinstance(action, dict):
                    action_text = action.get('change', str(action))
                else:
                    action_text = str(action)
                
                action_lower = action_text.lower()
                if any(keyword in action_lower for keyword in ['literature', 'reading', 'language arts', 'stories', 'books']):
                    ela_recs.append(action_text)
                elif any(keyword in action_lower for keyword in ['social studies', 'history', 'cultural', 'biography', 'historical']):
                    social_studies_recs.append(action_text)
                elif any(keyword in action_lower for keyword in ['science', 'technology', 'stem', 'biology', 'physics']):
                    science_recs.append(action_text)
                elif any(keyword in action_lower for keyword in ['health', 'lgbt', 'gender', 'identity']):
                    health_recs.append(action_text)
                else:
                    general_recs.append(action_text)
            
            if ela_recs:
                formatted += "#### English Language Arts\n"
                for rec in ela_recs:
                    formatted += f"- {rec}\n"
                formatted += "\n"
            
            if social_studies_recs:
                formatted += "#### Social Studies\n"
                for rec in social_studies_recs:
                    formatted += f"- {rec}\n"
                formatted += "\n"
            
            if science_recs:
                formatted += "#### Science & Technology\n"
                for rec in science_recs:
                    formatted += f"- {rec}\n"
                formatted += "\n"
            
            if health_recs:
                formatted += "#### Health Education\n"
                for rec in health_recs:
                    formatted += f"- {rec}\n"
                formatted += "\n"
            
            if general_recs:
                formatted += "#### General Curriculum\n"
                for rec in general_recs:
                    formatted += f"- {rec}\n"
                formatted += "\n"
        
        if "module_recommendations" in ai_result:
            formatted += "### Module-Specific Actions\n"
            for i, rec in enumerate(ai_result["module_recommendations"], 1):
                formatted += f"**{i}.** {rec}\n\n"
        
        if "implementation_timeline" in ai_result:
            formatted += f"### Implementation Timeline\n{ai_result['implementation_timeline']}\n\n"
        
        if "content_considerations" in ai_result:
            formatted += f"### Content Considerations\n{ai_result['content_considerations']}\n\n"
        
        if "progress_metrics" in ai_result:
            formatted += f"### Progress Metrics\n{ai_result['progress_metrics']}\n\n"
        
        return formatted
    
    def _generate_fallback_suggestions(self, analysis: Dict[str, Any], 
                                     module_name: str) -> str:
        """Generate rule-based suggestions when AI is unavailable"""
        
        suggestions = f"## Curriculum Content Recommendations for {module_name}\n\n"
        
        over_represented = []
        under_represented = []
        
        for demo, data in analysis['demographics'].items():
            gap = data['gap']
            if gap > 5:  # Over-represented by more than 5%
                over_represented.append((demo, gap, data['gap_count']))
            elif gap < -5:  # Under-represented by more than 5%
                under_represented.append((demo, abs(gap), abs(data['gap_count'])))
        
        # Add summary section after calculating over/under represented
        total_recs = len(over_represented) + len(under_represented)
        if total_recs > 0:
            suggestions += "### Summary of Imbalances\n"
            suggestions += f"- **Demographics needing attention:** {total_recs} groups\n"
            if under_represented:
                under_names = [demo for demo, _, _ in under_represented]
                suggestions += f"- **Underrepresented:** {', '.join(under_names)}\n"
            if over_represented:
                over_names = [demo for demo, _, _ in over_represented]
                suggestions += f"- **Overrepresented:** {', '.join(over_names)}\n"
            suggestions += "- **Recommended approach:** Content revision and character diversification\n\n"
        
        if over_represented and under_represented:
            suggestions += "### Priority Content Changes\n"
            
            # Sort by largest gaps
            over_represented.sort(key=lambda x: x[1], reverse=True)
            under_represented.sort(key=lambda x: x[1], reverse=True)
            
            # Create change cards
            change_count = 1
            for over_demo, over_gap, over_count in over_represented:
                for under_demo, under_gap, under_count in under_represented:
                    move_count = min(over_count, under_count)
                    move_pct = (move_count / analysis['total_people']) * 100
                    
                    if move_count > 0:
                        suggestions += f"#### Change {change_count}: {under_demo} Representation Enhancement\n"
                        suggestions += f"**Current Gap:** {under_demo} underrepresented by {under_gap:.1f}%\n\n"
                        suggestions += f"**Recommended Actions:**\n"
                        suggestions += f"- Revise {move_pct:.1f}% of content featuring {over_demo} characters\n"
                        suggestions += f"- Introduce {under_demo} protagonists in stories and case studies\n"
                        suggestions += f"- Add cultural themes and perspectives from {under_demo} communities\n"
                        suggestions += f"- Update visual materials to include {under_demo} representation\n\n"
                        change_count += 1
        
        # Add subject-specific recommendations
        suggestions += "### Content Strategies by Subject Area\n"
        
        suggestions += "#### English Language Arts\n"
        suggestions += "- Review reading lists for diverse authors and protagonists\n"
        suggestions += "- Include folktales and stories from various cultures\n"
        suggestions += "- Add vocabulary examples that reflect diverse experiences\n\n"
        
        suggestions += "#### Social Studies\n"
        suggestions += "- Feature historical figures from underrepresented groups\n"
        suggestions += "- Include multiple cultural perspectives on historical events\n"
        suggestions += "- Add case studies from diverse communities\n\n"
        
        suggestions += "#### Science & Technology\n"
        suggestions += "- Highlight scientists and inventors from various backgrounds\n"
        suggestions += "- Use diverse names in math problems and examples\n"
        suggestions += "- Include global perspectives on scientific discoveries\n\n"
        
        suggestions += "### Implementation Timeline\n"
        suggestions += "**Phase 1 (Months 1-3):** Audit current materials and identify priority changes\n\n"
        suggestions += "**Phase 2 (Months 4-8):** Implement content revisions in high-impact modules\n\n"
        suggestions += "**Phase 3 (Months 9-12):** Monitor progress and gather feedback for refinements\n"
        
        return suggestions
    
    def chat_interface(self, analysis: Dict[str, Any], user_question: str = None) -> str:
        """Interactive chat interface for demographic questions"""
        
        if not self.available:
            return "AI chat is currently unavailable. Please check your OpenAI API key configuration."
        
        if not user_question:
            return self.generate_balancing_suggestions(analysis)
        
        try:
            # Create context-aware prompt
            context = self._create_context_summary(analysis)
            
            full_prompt = f"""
            Context: {context}
            
            User Question: {user_question}
            
            Please provide a helpful response about demographic balancing strategies.
            Focus on actionable advice with specific numbers when possible.
            """
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an education equity assistant helping align K-8 curriculum modules with demographic representation goals. Focus only on instructional content (lessons, texts, visuals, characters, stories, themes), not staffing or HR-related topics."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.4
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Unable to process your question at the moment: {e}"
    
    def _create_context_summary(self, analysis: Dict[str, Any]) -> str:
        """Create summary context for chat"""
        
        context = f"Dataset has {analysis['total_people']:,} total people. "
        
        gaps = []
        for demo, data in analysis['demographics'].items():
            if abs(data['gap']) > 2:
                status = "over" if data['gap'] > 0 else "under"
                gaps.append(f"{demo} is {status}-represented by {abs(data['gap']):.1f}%")
        
        if gaps:
            context += "Key gaps: " + "; ".join(gaps)
        else:
            context += "Demographics are well-balanced overall."
        
        return context

def create_chatbot_interface(df: pd.DataFrame, demographic_cols: List[str], 
                           targets: Dict[str, float]):
    """Create Streamlit interface for the demographic chatbot"""
    
    st.subheader("AI Curriculum Content Advisor")
    
    chatbot = DemographicChatbot()
    
    if not chatbot.available:
        st.warning("AI curriculum advisor requires OpenAI API key. Please configure in environment settings.")
        return
    
    # Analyze current state
    analysis = chatbot.analyze_demographic_gaps(df, demographic_cols, targets)
    
    # Chat interface
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display automatic analysis
    if st.button("Get Content Recommendations", type="primary"):
        with st.spinner("Analyzing curriculum representation..."):
            recommendations = chatbot.generate_balancing_suggestions(analysis)
            st.session_state.chat_history.append({
                "type": "ai_analysis", 
                "content": recommendations
            })
    
    # Custom question input
    user_question = st.text_input(
        "Ask about curriculum content changes:",
        placeholder="e.g., How can I update lessons to better represent Asian characters and themes?"
    )
    
    if st.button("Ask Question") and user_question:
        with st.spinner("Generating response..."):
            response = chatbot.chat_interface(analysis, user_question)
            st.session_state.chat_history.append({
                "type": "question",
                "content": user_question
            })
            st.session_state.chat_history.append({
                "type": "response", 
                "content": response
            })
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Conversation History")
        
        for i, message in enumerate(reversed(st.session_state.chat_history[-6:])):  # Show last 6 messages
            if message["type"] == "question":
                st.write(f"**You:** {message['content']}")
            elif message["type"] == "response":
                st.write(f"**Curriculum Advisor:** {message['content']}")
            elif message["type"] == "ai_analysis":
                st.markdown(message['content'])
            
            if i < len(st.session_state.chat_history) - 1:
                st.divider()
    
    # Clear chat history button
    if st.session_state.chat_history and st.button("Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()