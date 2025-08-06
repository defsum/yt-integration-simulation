"""
simple AI comment generation engine
"""

import random
from typing import Dict
from faker import Faker

from .models import Comment
from apps.videos.models import Video


class YouTubeAICommentEngine:
    
    def __init__(self):
        self.fake = Faker()
        
        # system message template with ${offer-info} placeholder
        self.business_reply_template = """You are responding as the channel owner. Be friendly and helpful. ${offer-info}"""
        
        # comment templates
        self.comment_templates = [
            "Great video!",
            "This is really helpful, thanks!",
            "Love this content!",
            "First time I understood this topic.",
            "Can you do more tutorials like this?",
            "Amazing explanation!",
            "This helped me a lot.",
            "Keep up the great work!",
            "Exactly what I was looking for.",
            "Perfect timing, I needed this."
        ]
        
        # business offers for demo
        self.offers = [
            {
                'name': 'TechMaster Course',
                'info': 'Online programming course. $99 (50% off). Link: techcourse.com/discount',
                'keywords': ['programming', 'coding', 'tech', 'learn']
            },
            {
                'name': 'Marketing Guide',
                'info': 'Digital marketing ebook. $29. Link: marketing-guide.com/buy',
                'keywords': ['marketing', 'business', 'grow']
            }
        ]

    def generate_user_comment(self, video: Video) -> Comment:
        content = random.choice(self.comment_templates)
        
        comment = Comment.objects.create(
            video=video,
            content=content,
            author_name=self.fake.name(),
            is_ai_generated=False,  # these simulate real users, so they should be analyzed
            ai_model_used='simple_user_simulation',
            like_count=random.randint(0, 10)
        )
        
        return comment

    def analyze_comment_for_business_opportunity(self, comment: Comment) -> Dict:
        content = comment.content.lower()
        
        # skip AI-generated comments
        if comment.is_ai_generated:
            return {
                'should_reply': False,
                'confidence': 0.0,
                'matched_offers': [],
                'reply_type': None,
                'reasoning': 'Skipping AI-generated comment'
            }
        
        # skip if channel already replied
        if comment.replies.filter(author_name=comment.video.channel_name).exists():
            return {
                'should_reply': False,
                'confidence': 0.0,
                'matched_offers': [],
                'reply_type': None,
                'reasoning': 'Channel already replied'
            }
        
        # simple opportunity detection
        positive_words = ['great', 'helpful', 'love', 'amazing', 'perfect', 'thanks']
        question_words = ['how', 'can you', 'tutorial', 'more']
        
        has_positive = any(word in content for word in positive_words)
        has_question = any(word in content for word in question_words)
        is_first = 'first' in content
        
        # Find matching offers
        matched_offers = []
        for offer in self.offers:
            if any(keyword in content for keyword in offer['keywords']):
                matched_offers.append(offer)
        
        # simple confidence scoring
        confidence = 0.0
        if has_positive:
            confidence += 0.3
        if has_question:
            confidence += 0.4
        if is_first:
            confidence += 0.5
        if matched_offers:
            confidence += 0.3
        
        should_reply = confidence >= 0.3
        
        # determine reply type
        reply_type = None
        if is_first:
            reply_type = 'first_comment'
        elif has_question:
            reply_type = 'question'
        elif has_positive:
            reply_type = 'positive'
        else:
            reply_type = 'general'
        
        return {
            'should_reply': should_reply,
            'confidence': min(confidence, 1.0),
            'matched_offers': matched_offers,
            'reply_type': reply_type,
            'reasoning': ''
        }

    def generate_business_reply(self, user_comment: Comment, analysis: Dict) -> Comment:

        reply_templates = {
            'first_comment': [
                "Thanks for being first! I appreciate early viewers.",
                "First! Love the enthusiasm.",
            ],
            'question': [
                "Great question! I have more content on this coming soon.",
                "Thanks for asking! This is covered in my other videos.",
            ],
            'positive': [
                "Thank you! Comments like yours motivate me to keep creating.",
                "Really appreciate the kind words!",
            ],
            'general': [
                "Thanks for watching!",
                "Appreciate the engagement!",
            ]
        }
        
        reply_type = analysis.get('reply_type', 'general')
        base_reply = random.choice(reply_templates.get(reply_type, reply_templates['general']))
        
        # add offer if available
        if analysis['matched_offers']:
            offer = analysis['matched_offers'][0]
            reply_content = f"{base_reply} Since you're interested, check out my {offer['name']}: {offer['info']}"
        else:
            reply_content = base_reply
        
        # seed for consistent variation
        variation_seed = user_comment.id % len(reply_templates[reply_type])
        reply_content = reply_templates[reply_type][variation_seed]
        
        if analysis['matched_offers']:
            offer = analysis['matched_offers'][0]
            reply_content += f" You might like my {offer['name']}: {offer['info']}"
        
        reply = Comment.objects.create(
            video=user_comment.video,
            parent_comment=user_comment,
            content=reply_content,
            author_name=user_comment.video.channel_name,
            author_avatar_url=user_comment.video.channel_avatar_url,
            is_ai_generated=True,
            ai_model_used='simple_business_reply',
            like_count=random.randint(0, 5)
        )
        
        return reply

    def generate_channel_promotional_comment(self, video: Video, offer_type: str = None) -> Comment:
        offer = random.choice(self.offers)
        
        promo_templates = [
            f"Hey everyone! Thanks for watching. I've created {offer['name']} for viewers who want to go deeper: {offer['info']}",
            f"Loving the engagement on this video! For those interested, check out {offer['name']}: {offer['info']}",
        ]
        
        content = random.choice(promo_templates)
        
        promo_comment = Comment.objects.create(
            video=video,
            content=content,
            author_name=video.channel_name,
            author_avatar_url=video.channel_avatar_url,
            is_ai_generated=True,
            ai_model_used='simple_channel_promo',
            like_count=random.randint(5, 15)
        )
        
        return promo_comment


youtube_ai_engine = YouTubeAICommentEngine()