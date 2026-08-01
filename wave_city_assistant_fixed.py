"""
Wave City WhatsApp AI Assistant
Real Estate Sales Chatbot with Lead Scoring, Smart Alternatives & Fraud Detection
Version 4.0 - FIXED & READY TO RUN - WITH CLAUDE AI INTEGRATION
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from enum import Enum

# ============================================================
# CLAUDE API CONFIGURATION - ADD YOUR KEY HERE
# ============================================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "sk-ant-xxxxxxxxxxxxxxxx")  # Replace with your key

# Try to import Anthropic client
try:
    import anthropic  # type: ignore[import]
    CLAUDE_AVAILABLE = True
except ImportError:
    anthropic = None  # type: ignore[assignment]
    CLAUDE_AVAILABLE = False
    print("⚠️  Warning: anthropic library not installed. Install with: pip install anthropic")
    print("   Falling back to rule-based responses...")


class LeadScore(Enum):
    HOT_BUYER = "HOT_BUYER"
    WARM_LEAD = "WARM_LEAD"
    INVESTOR = "INVESTOR"
    CASUAL_BROWSER = "CASUAL_BROWSER"


class ConversationManager:
    """Main AI Assistant Engine for Wave City Real Estate"""
    
    def __init__(self):
        self.properties = self._load_properties()
        self.wave_city_info = self._load_area_knowledge()
        self.conversation_history = {}
        self.lead_scores = {}
        
        # Initialize Claude client if available
        self.claude_client = None
        self.use_claude = False
        
        if CLAUDE_AVAILABLE and ANTHROPIC_API_KEY != "sk-ant-xxxxxxxxxxxxxxxx":
            try:
                self.claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                self.use_claude = True
                print("✅ Claude AI Integration: ACTIVE")
            except Exception as e:
                print(f"⚠️  Claude initialization failed: {e}")
                print("   Falling back to rule-based responses...")
                self.use_claude = False
        
    def _load_properties(self) -> List[Dict]:
        """Load property listings - Replace with your actual properties"""
        return [
            {
                "id": "EDEN001",
                "name": "3 BHK Apartment - Wave Eden",
                "floor": "4th Floor",
                "tower": "Tower B",
                "size_sqft": 1450,
                "price_lakhs": 65,
                "status": "Ready to Move",
                "highlights": ["Park facing", "Corner unit", "Modular kitchen included"],
                "bhk": 3,
                "property_type": "Apartment"
            },
            {
                "id": "DREAM001",
                "name": "2 BHK Apartment - Wave Dream Homes",
                "floor": "5th Floor",
                "tower": "Tower A",
                "size_sqft": 950,
                "price_lakhs": 42,
                "status": "Ready to Move",
                "highlights": ["Ground floor", "Parking included", "Gated block"],
                "bhk": 2,
                "property_type": "Apartment"
            },
            {
                "id": "PLOT001",
                "name": "Residential Plot - Phase 2",
                "size_sqyards": 100,
                "price_lakhs": 28,
                "status": "Registry done, clear title",
                "highlights": ["Corner plot", "Main road facing", "All utilities connected"],
                "property_type": "Plot"
            },
            {
                "id": "EXEC001",
                "name": "2 BHK Executive Floor",
                "size_sqft": 950,
                "price_lakhs": 38,
                "status": "Ready to Move",
                "highlights": ["Corner plot", "Parking included", "Gated block"],
                "bhk": 2,
                "property_type": "Executive Floor"
            },
            {
                "id": "ELIGO001",
                "name": "3 BHK Apartment - Wave Eligo",
                "floor": "8th Floor",
                "size_sqft": 1400,
                "price_lakhs": 58,
                "status": "Under Construction",
                "highlights": ["Mid-rise", "Spacious layout", "Study room option"],
                "bhk": 3,
                "property_type": "Apartment"
            }
        ]
    
    def _load_area_knowledge(self) -> Dict:
        """Wave City area information"""
        return {
            "location": "NH-24, Ghaziabad (near Govindpuram)",
            "total_area_acres": 4200,
            "developed_acres": 2057,
            "families_residing": 22000,
            "connectivity": {
                "akshardham": "~20 minutes",
                "noida_sector_62": "~12 minutes",
                "anand_vihar": "~30 minutes",
                "ghaziabad_railway": "~3 km",
                "vaishali_metro": "~12 km",
                "airport": "~50 km"
            },
            "amenities": [
                "Clubhouse", "Swimming pool", "Gymnasium", "SportZon (cricket, tennis, football)",
                "Golf range", "Cycling/jogging tracks", "Schools", "Hospitals", "Retail zones"
            ],
            "features": [
                "Platinum-rated Green Township",
                "UP RERA approved",
                "Smart infrastructure (fiber, smart grid, CCTV, automated lighting)",
                "24/7 power backup",
                "Rainwater harvesting & solar power"
            ]
        }
    
    def initialize_user(self, user_id: str, name: str = None):
        """Initialize conversation for new user"""
        self.conversation_history[user_id] = {
            "messages": [],
            "user_name": name,
            "budget": None,
            "bhk_preference": None,
            "purpose": None,
            "timeline": None,
            "loan_status": None,
            "visit_ready": False,
            "fraud_flags": []
        }
        self.lead_scores[user_id] = {
            "response_speed": 0,
            "budget_clarity": 0,
            "repeat_visits": 0,
            "loan_readiness": 0,
            "engagement_level": 0
        }
    
    def process_message(self, user_id: str, message: str) -> str:
        """Main function to process incoming message and generate response"""
        
        if user_id not in self.conversation_history:
            self.initialize_user(user_id)
        
        fraud_detected = self._detect_fraud(user_id, message)
        if fraud_detected:
            return fraud_detected
        
        self.conversation_history[user_id]["messages"].append({
            "timestamp": datetime.now().isoformat(),
            "sender": "user",
            "text": message
        })
        
        self._extract_buyer_info(user_id, message)
        self._update_lead_score(user_id, message)
        
        response = self._generate_response(user_id, message)
        
        self.conversation_history[user_id]["messages"].append({
            "timestamp": datetime.now().isoformat(),
            "sender": "assistant",
            "text": response
        })
        
        return response
    
    def _detect_fraud(self, user_id: str, message: str) -> Optional[str]:
        """Fraud detection system"""
        msg_lower = message.lower()
        
        if any(phrase in msg_lower for phrase in [
            "absolute lowest price", "dealer price", "commission sharing",
            "builder direct contact", "price list of all properties"
        ]):
            self.conversation_history[user_id]["fraud_flags"].append("PRICE_FISHING")
            return ("Thank you for your inquiry. Our pricing is fixed as per the current market rate "
                   "and is available upon a scheduled consultation. If you are a channel partner, "
                   "kindly share your RERA registration number and we will connect you with our "
                   "partnership team.")
        
        if any(phrase in msg_lower for phrase in [
            "full address", "exact location", "floor plan pdf", "registry documents",
            "sale deed", "allotment letter", "owner's contact", "unsold units"
        ]):
            self.conversation_history[user_id]["fraud_flags"].append("DATA_HARVESTING")
            return ("For security and privacy reasons, detailed documents and ownership information "
                   "are shared only during a verified in-person or video consultation. I would be "
                   "happy to arrange that — may I know your name and preferred time?")
        
        if any(phrase in msg_lower for phrase in [
            "send money", "bank account", "upi id", "crypto", "gift card",
            "foreign transfer", "cheque", "above market price"
        ]):
            self.conversation_history[user_id]["fraud_flags"].append("PAYMENT_SCAM")
            return ("All payments and financial transactions are conducted exclusively through "
                   "official, verified channels and only after a site visit and documentation review. "
                   "We do not process any advance payments via chat. Kindly contact our office directly.")
        
        if any(phrase in msg_lower for phrase in [
            "rera authority", "government", "legal officer", "court appointed",
            "bank agent", "wave city developer office"
        ]):
            self.conversation_history[user_id]["fraud_flags"].append("IMPERSONATION")
            return ("For any official or legal matters related to Wave City, kindly contact the "
                   "Wave City customer care or UP RERA directly. We are an independent sales agency.")
        
        if any(phrase in msg_lower for phrase in [
            "expose", "post bad reviews", "threaten", "sue", "lawyer"
        ]) and any(word in msg_lower for word in ["unless", "if not", "or else"]):
            self.conversation_history[user_id]["fraud_flags"].append("AGGRESSIVE_BEHAVIOR")
            return ("I appreciate your interest. However, we maintain professional communication standards. "
                   "Our team will reach out to you directly. Thank you.")
        
        return None
    
    def _extract_buyer_info(self, user_id: str, message: str):
        """Extract buyer information from messages"""
        import re
        msg_lower = message.lower().strip()
        history = self.conversation_history[user_id]
        
        # ── Smart budget extraction ──
        budget = self._extract_budget(msg_lower)
        if budget:
            history["budget"] = budget
        elif self._is_ambiguous_budget(msg_lower):
            history["budget_clarification_needed"] = True
        
        for bhk in [1, 2, 3, 4, 5]:
            if f"{bhk} bhk" in msg_lower or f"{bhk}bhk" in msg_lower:
                history["bhk_preference"] = bhk
                break
        
        if any(word in msg_lower for word in ["investment", "investor", "rental yield", "appreciation"]):
            history["purpose"] = "investment"
        elif any(word in msg_lower for word in ["self", "own", "live", "family", "home"]):
            history["purpose"] = "self-use"
        
        if any(word in msg_lower for word in ["soon", "urgent", "asap", "immediately", "this week"]):
            history["timeline"] = "urgent"
        elif any(word in msg_lower for word in ["next month", "next quarter", "3 months"]):
            history["timeline"] = "medium"
        elif any(word in msg_lower for word in ["next year", "whenever", "planning ahead"]):
            history["timeline"] = "flexible"
        
        if any(word in msg_lower for word in ["loan", "emi", "home loan", "finance", "mortgage"]):
            if "cash" in msg_lower and "loan" not in msg_lower:
                history["loan_status"] = "cash_only"
            else:
                history["loan_status"] = "open_to_loan"
        
        if any(word in msg_lower for word in ["visit", "see", "come", "arrange", "schedule"]):
            history["visit_ready"] = True
    
    def _extract_budget(self, msg: str) -> Optional[float]:
        """Smart budget extractor — handles lakhs, crores, K, raw numbers"""
        import re
        
        # Crores — "1.5 cr", "2 crore"
        cr = re.search(r'(\d+\.?\d*)\s*(?:cr|crore|crores)', msg)
        if cr:
            return round(float(cr.group(1)) * 100, 2)
        
        # Lakhs — "45L", "45 lakh", "₹45 lakh"
        lakh = re.search(r'₹?\s*(\d+\.?\d*)\s*(?:l\b|lakh|lakhs)', msg)
        if lakh:
            return round(float(lakh.group(1)), 2)
        
        # Thousands — "500k"
        k = re.search(r'(\d+\.?\d*)\s*k\b', msg)
        if k:
            return round(float(k.group(1)) / 100, 2)
        
        # Raw large numbers — "5000000", "50,00,000"
        raw = re.sub(r'[,\s]', '', msg)
        raw_match = re.search(r'(\d{6,})', raw)
        if raw_match:
            return round(int(raw_match.group(1)) / 100000, 2)
        
        # Ambiguous with keyword — "budget 60", "around 80"
        ambiguous = re.search(
            r'(?:budget|price|around|approx|upto|within|max)\s*(?:of|is|around)?\s*₹?\s*(\d+\.?\d*)', msg
        )
        if ambiguous:
            val = float(ambiguous.group(1))
            if val < 10:
                return None   # too ambiguous — ask user
            elif 10 <= val <= 99:
                # Could be lakhs OR crores — ask user for clarification
                return None   # Trigger budget_clarification_needed
            elif val <= 500:
                return round(val, 2)       # assume lakhs
            elif val <= 9999:
                return round(val / 100, 2) # thousands → lakhs
            else:
                return round(val / 100000, 2)
        
        return None
    
    def _is_ambiguous_budget(self, msg: str) -> bool:
        """Detect if user said a number with no unit"""
        import re
        return bool(re.search(
            r'(?:budget|price)\s*(?:is|around|of)?\s*₹?\s*(\d+)\s*$', msg
        ))
    
    def _update_lead_score(self, user_id: str, message: str):
        """Update lead scoring based on conversation"""
        scores = self.lead_scores[user_id]
        history = self.conversation_history[user_id]
        
        if len(history["messages"]) <= 2:
            scores["response_speed"] = 9
        
        if history["budget"]:
            scores["budget_clarity"] = 9
        elif any(word in message.lower() for word in ["around", "approximately", "range"]):
            scores["budget_clarity"] = 6
        else:
            scores["budget_clarity"] = max(scores["budget_clarity"], 3)
        
        msg_count = len(history["messages"]) // 2
        if msg_count > 2:
            scores["repeat_visits"] = 8
        elif msg_count == 1:
            scores["repeat_visits"] = 4
        
        if history["loan_status"] == "open_to_loan":
            scores["loan_readiness"] = 8
        elif history["loan_status"] == "cash_only":
            scores["loan_readiness"] = 5
        else:
            scores["loan_readiness"] = 2
        
        msg_lower = message.lower()
        if any(word in msg_lower for word in ["specific", "which", "what about", "tell me", "details"]):
            scores["engagement_level"] = 9
        elif history["bhk_preference"] or history["budget"]:
            scores["engagement_level"] = 7
        else:
            scores["engagement_level"] = 3
    
    def get_lead_classification(self, user_id: str) -> Tuple[LeadScore, int]:
        """Classify lead based on scores"""
        scores = self.lead_scores[user_id]
        average = sum(scores.values()) / len(scores)
        
        if average >= 70:
            return LeadScore.HOT_BUYER, int(average)
        elif average >= 45:
            return LeadScore.WARM_LEAD, int(average)
        elif self.conversation_history[user_id]["purpose"] == "investment":
            return LeadScore.INVESTOR, int(average)
        else:
            return LeadScore.CASUAL_BROWSER, int(average)
    
    def _generate_claude_response(self, user_id: str, message: str) -> Optional[str]:
        """Generate response using Claude AI - Returns None if Claude not available"""
        if not self.use_claude or not self.claude_client:
            return None
        
        try:
            history = self.conversation_history[user_id]
            lead_class, score = self.get_lead_classification(user_id)
            
            # Build conversation context for Claude
            recent_messages = history["messages"][-5:] if len(history["messages"]) > 5 else history["messages"]
            conversation_context = "\n".join([
                f"Customer: {msg['text']}" if msg['role'] == 'user' else f"Bot: {msg['text']}"
                for msg in recent_messages
            ])
            
            # Create system prompt for Claude
            system_prompt = f"""You are Priyanshu's AI Assistant for Wave City Real Estate, Ghaziabad.
            
IMPORTANT RULES:
1. Keep responses professional, formal, and concise
2. Always be helpful and never say "we don't have that" - suggest alternatives
3. Focus on Wave City properties in NH-24, Ghaziabad
4. Lead Classification: {lead_class.value} (Score: {score}/100)
5. Customer Budget: ₹{history['budget']} Lakhs (if specified)
6. Customer BHK Preference: {history['bhk_preference']} BHK (if specified)
7. Never negotiate on price - offer to connect with Priyanshu instead
8. Always end with a next step (visit scheduling, callback, or more info)

Available Properties:
{json.dumps(self.properties, indent=2)}

Recent Conversation:
{conversation_context}

Generate a helpful, professional response that:
- Answers the customer's question
- Follows all rules above
- Suggests smart alternatives if exact match not available
- Keeps the conversation warm and moving forward"""

            # Call Claude API
            message_obj = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            
            return message_obj.content[0].text
        
        except Exception as e:
            print(f"⚠️  Claude API error: {e}")
            return None
    
    def _generate_response(self, user_id: str, message: str) -> str:
        """Generate contextual response based on conversation state
        
        Order of precedence:
        1. Try Claude AI if available
        2. Fall back to rule-based responses
        """
        
        # Try Claude AI first if enabled
        if self.use_claude:
            claude_response = self._generate_claude_response(user_id, message)
            if claude_response:
                return claude_response
        
        # Fall back to rule-based responses
        history = self.conversation_history[user_id]
        lead_class, score = self.get_lead_classification(user_id)
        
        if len(history["messages"]) <= 2:
            return self._greeting_response()
        
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ["which", "what property", "show me", "available"]):
            return self._property_inquiry_response(user_id)
        
        if "price" in msg_lower or "₹" in message or "cost" in msg_lower:
            return self._price_inquiry_response(user_id)
        
        if any(word in msg_lower for word in ["location", "connectivity", "nearby", "distance", "metro"]):
            return self._area_inquiry_response()
        
        if "visit" in msg_lower or "schedule" in msg_lower or "meet" in msg_lower:
            return self._visit_scheduling_response(user_id)
        
        if any(word in msg_lower for word in ["amenities", "facilities", "gym", "pool", "school", "hospital"]):
            return self._amenities_response()
        
        if "investment" in msg_lower or "return" in msg_lower or "appreciation" in msg_lower:
            return self._investment_response()
        
        if "loan" in msg_lower or "emi" in msg_lower or "finance" in msg_lower:
            return self._loan_response()
        
        if "rera" in msg_lower or "legal" in msg_lower or "approved" in msg_lower:
            return self._rera_response()
        
        return self._clarifying_question(user_id)
    
    def _greeting_response(self) -> str:
        return (
            "🏠 Namaste! Welcome to Wave City, Ghaziabad — NCR's finest planned township on NH-24.\n\n"
            "I'm here to assist you with our premium residential properties. We offer:\n"
            "✅ Ready-to-move & Under-construction apartments (1-3 BHK)\n"
            "✅ Executive Floors & Luxury Skyvillas\n"
            "✅ Residential Plots\n\n"
            "To help you better, may I ask:\n"
            "1️⃣ What is your approximate budget?\n"
            "2️⃣ Are you looking for a 1, 2, or 3+ BHK property?\n\n"
            "I'm also happy to schedule a site visit or share more details about our township. "
            "What interests you most?"
        )
    
    def _property_inquiry_response(self, user_id: str) -> str:
        history = self.conversation_history[user_id]
        budget = history.get("budget")
        bhk = history.get("bhk_preference")
        
        matching = self._find_matching_properties(budget, bhk)
        
        if matching:
            response = "🏡 Here are the properties that match your criteria:\n\n"
            for prop in matching[:3]:
                response += self._format_property(prop) + "\n"
            response += "\nWould you like to visit any of these properties, or shall I suggest alternatives?"
            return response
        else:
            return self._suggest_alternative(user_id)
    
    def _find_matching_properties(self, budget: int = None, bhk: int = None) -> List[Dict]:
        """Find properties matching buyer criteria"""
        results = self.properties
        
        if budget:
            results = [p for p in results if p.get("price_lakhs", 0) <= budget + 10]
        
        if bhk:
            results = [p for p in results if p.get("bhk", 0) == bhk]
        
        return sorted(results, key=lambda x: x.get("price_lakhs", 0))
    
    def _suggest_alternative(self, user_id: str) -> str:
        """Smart alternative suggestion engine"""
        history = self.conversation_history[user_id]
        
        if history["budget"] and history["budget"] < 30:
            return (
                "I understand you're looking for a property within ₹" + str(history["budget"]) + " Lakhs. "
                "Our most affordable option is the Wave Dream Homes 2 BHK at ₹42 Lakhs — "
                "same township, same world-class amenities, just a bit more within your reach. "
                "It's ready to move and perfectly suited for first-time buyers.\n\n"
                "Would you like to know more or schedule a visit?"
            )
        
        if history["bhk_preference"] == 4:
            return (
                "I understand you're looking for a 4 BHK. While our luxury 4 & 5 BHK skyvillas in "
                "Wave Veridia are available, our exceptionally spacious 3 BHK units in Wave Eligo "
                "often feel like 4 rooms — many include a study/utility space. At a better price point "
                "and faster possession.\n\n"
                "Would you like to explore that?"
            )
        
        return (
            "Based on what you've shared, our Wave Eden 3 BHK at ₹65 Lakhs is our most popular choice — "
            "perfectly balanced between space, price, and location. Ready to move.\n\n"
            "Would you like details or to arrange a visit?"
        )
    
    def _format_property(self, prop: Dict) -> str:
        """Format property details for display"""
        details = f"📍 {prop['name']}\n"
        
        if "floor" in prop:
            details += f"   Floor: {prop['floor']}\n"
        if "size_sqft" in prop:
            details += f"   Size: {prop['size_sqft']} sq.ft\n"
        if "size_sqyards" in prop:
            details += f"   Size: {prop['size_sqyards']} sq.yards\n"
        
        details += f"   💰 Price: ₹{prop['price_lakhs']} Lakhs\n"
        details += f"   Status: {prop['status']}\n"
        
        if prop['highlights']:
            details += f"   ✨ Highlights: {', '.join(prop['highlights'][:2])}\n"
        
        return details
    
    def _price_inquiry_response(self, user_id: str) -> str:
        history = self.conversation_history[user_id]
        
        if history["messages"] and "reduce" in history["messages"][-2].get("text", "").lower():
            return (
                "I appreciate your interest! For any negotiation or special pricing discussions, "
                "I'd like to connect you directly with our senior property consultant Priyanshu. "
                "He can explore all available options for you.\n\n"
                "What's your preferred callback time — morning (10am–1pm) or afternoon (2pm–6pm)?"
            )
        
        return (
            "Our pricing is fixed as per current market rates and varies based on property type, "
            "location within the township, and possession timeline.\n\n"
            "To give you accurate pricing, could you share:\n"
            "• Your budget range\n"
            "• Preferred BHK configuration\n"
            "• Ready-to-move or under-construction?\n\n"
            "This will help me suggest the best options for you."
        )
    
    def _area_inquiry_response(self) -> str:
        return (
            "📍 Wave City Connectivity (from NH-24):\n"
            "🚗 Akshardham Temple, Delhi: ~20 minutes\n"
            "🚗 Noida Sector 62 (IT Hub): ~12 minutes\n"
            "🚗 Anand Vihar ISBT: ~30 minutes\n"
            "🚄 Vaishali Metro Station: ~12 km\n"
            "✈️ IGI Airport: ~50 km\n"
            "🚂 Ghaziabad Railway Station: ~3 km\n\n"
            "Wave City is strategically located on NH-24 with seamless access to Delhi, Noida, "
            "and surrounding areas. Perfect for professionals and families!\n\n"
            "Would you like to schedule a visit to experience the location firsthand?"
        )
    
    def _visit_scheduling_response(self, user_id: str) -> str:
        return (
            "🎯 Great! Let's schedule your site visit.\n\n"
            "Please share:\n"
            "1️⃣ Your preferred date\n"
            "2️⃣ Time slot — Morning (10am–1pm) or Afternoon (2pm–6pm)?\n"
            "3️⃣ Your contact number\n\n"
            "Our consultant will confirm your visit shortly. "
            "You'll get to see our amenities, tour the available units, and meet our team!\n\n"
            "Looking forward to showing you Wave City. 🏡"
        )
    
    def _amenities_response(self) -> str:
        return (
            "🏊 Wave City Amenities:\n\n"
            "🏋️ Fitness: Gymnasium, swimming pool, yoga studio\n"
            "⚽ Sports: Cricket pitches, tennis courts, football ground, skating rink, golf range (5-hole)\n"
            "🚴 Recreation: Cycling & jogging tracks throughout township\n"
            "🎓 Community: Grand clubhouse, kids play areas, senior citizen zone\n"
            "🏥 Health: Hospitals nearby (Manipal, Sarvodaya, Santosh Speciality)\n"
            "🏫 Education: Quality schools within township (Gurukul, Campus, Brightland)\n"
            "🛍️ Shopping: The Opulent Mall, Avantika Market, Gaur Central Mall\n"
            "🌳 Environment: 1,470+ acres of green spaces, parks, landscaping\n\n"
            "All supported by smart infrastructure: fiber internet, 24/7 power backup, CCTV security, "
            "automated lighting. A complete lifestyle destination! 🌟\n\n"
            "Would you like to experience these amenities firsthand?"
        )
    
    def _investment_response(self) -> str:
        return (
            "💼 Wave City Investment Highlights:\n\n"
            "📈 Steady Price Appreciation: Consistent growth over recent years\n"
            "👨‍👩‍👧‍👦 Established Community: 22,000+ families, 15,600+ units sold\n"
            "🏗️ Largest Planned Township: 4,200 acres — scale ensures long-term appreciation\n"
            "✅ Legal Security: All projects UP RERA-approved\n"
            "📍 Strategic Location: NH-24, proximity to Delhi & Noida IT hubs\n"
            "🎯 High Demand: Strong rental market due to connectivity\n\n"
            "Investors often focus on 2-3 BHK apartments for rental income, or plots for long-term capital appreciation.\n\n"
            "Based on your investment goals, I can recommend the best options. "
            "What's your expected holding period and return target?"
        )
    
    def _loan_response(self) -> str:
        return (
            "🏦 Home Loan Assistance:\n\n"
            "Most properties in Wave City qualify for standard home loan schemes. "
            "Common options include:\n"
            "• SBI Home Loan\n"
            "• HDFC, ICICI, Axis Bank\n"
            "• LIC, PNB Housing Finance\n\n"
            "Eligibility typically: 50-90% of property cost | Tenure: 5-20 years | "
            "Interest rates: Currently 7-8.5% per annum\n\n"
            "For personalized loan guidance and fastest approval, I'll connect you with our "
            "senior consultant Priyanshu, who works with multiple banks.\n\n"
            "What's your approximate monthly EMI capacity?"
        )
    
    def _rera_response(self) -> str:
        return (
            "✅ Legal & RERA Status:\n\n"
            "All residential projects in Wave City are registered under UP RERA — "
            "ensuring complete buyer protection and legal compliance.\n\n"
            "This means:\n"
            "✓ Your money is protected in escrow accounts\n"
            "✓ Timeline & quality commitments are legally enforceable\n"
            "✓ Complete transparency in construction progress\n"
            "✓ Full legal documentation at completion\n\n"
            "Wave City is one of India's first Platinum-rated Green Townships with all certifications in place.\n\n"
            "For any specific legal documentation, our consultant can arrange a detailed review during your visit."
        )
    
    def _clarifying_question(self, user_id: str) -> str:
        history = self.conversation_history[user_id]
        
        # Check for ambiguous budget first
        if history.get("budget_clarification_needed"):
            return (
                "Ek quick clarification — aapka budget "
                "Lakhs mein hai ya Crores mein? 😊\n"
                "Example: '45 Lakhs' or '1.5 Crore'"
            )
        
        if not history["budget"]:
            return "To suggest the best properties, could you share your approximate budget? 💰"
        elif not history["bhk_preference"]:
            return "What BHK configuration are you looking for — 1, 2, or 3+ BHK? 🏠"
        elif not history["purpose"]:
            return "Are you looking for self-use or as an investment? 📈"
        elif not history["timeline"]:
            return "When are you planning to move or invest? ⏰"
        else:
            return (
                "You've shared great details! Would you like me to:\n"
                "1️⃣ Share specific property options\n"
                "2️⃣ Arrange a site visit\n"
                "3️⃣ Answer more questions about Wave City\n\n"
                "What would help you most?"
            )
    
    def get_conversation_summary(self, user_id: str) -> Dict:
        """Get summary of conversation for agent handoff"""
        history = self.conversation_history[user_id]
        lead_class, score = self.get_lead_classification(user_id)
        
        return {
            "user_id": user_id,
            "user_name": history["user_name"],
            "lead_classification": lead_class.value,
            "lead_score": score,
            "budget": history["budget"],
            "bhk_preference": history["bhk_preference"],
            "purpose": history["purpose"],
            "timeline": history["timeline"],
            "visit_ready": history["visit_ready"],
            "fraud_flags": history["fraud_flags"],
            "message_count": len(history["messages"]),
            "conversation_timestamp": datetime.now().isoformat()
        }


def main():
    """Example usage of the Wave City Assistant"""
    
    assistant = ConversationManager()
    user_id = "user_123"
    
    messages = [
        "Hi, I'm interested in a property in Wave City",
        "I'm looking for a 2 BHK apartment, budget around 45 lakhs",
        "What's the connectivity like from Wave City?",
        "I'd like to schedule a visit"
    ]
    
    print("=" * 60)
    print("WAVE CITY WHATSAPP AI ASSISTANT - DEMO")
    print("=" * 60)
    
    for msg in messages:
        print(f"\n👤 User: {msg}")
        response = assistant.process_message(user_id, msg)
        print(f"\n🤖 Assistant:\n{response}")
        print("\n" + "-" * 60)
    
    summary = assistant.get_conversation_summary(user_id)
    print("\n📊 LEAD SUMMARY FOR AGENT:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
