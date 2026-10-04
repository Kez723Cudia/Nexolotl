from django.contrib.auth import get_user_model 
from django.test import TestCase 
from django.urls import reverse 
from friends.models import Friendship 
from testimonials.models import testimonial 
from .models import Profile 

User = get_user_model() 

class ProfileTestimonialSecurityTests(TestCase): 
    def setUp(self): 
        self.user = User.objects.create_user( 
            username="test_user", 
            email="test_user@example.com", 
            password="TestPassword123!", 
        ) 
        
        self.client.force_login(self.user) 
        
    def test_user_cannot_submit_testimonial_to_own_profile(self): 
        profile_url = reverse( 
            "profile", 
            kwargs={"username": self.user.username}, 
        ) 
            
        response = self.client.post( 
            profile_url, 
            {"content": "Self-written testimonial"}, 
        ) 
        self.assertEqual(response.status_code, 200) 

        self.assertFalse( 
            testimonial.objects.filter( 
                author=self.user, 
                recipient=self.user, 
            ).exists() 
        ) 

class FriendListPrivacyTests(TestCase): 
    def setUp(self): 
        self.owner = User.objects.create_user( 
            username="owner", 
            email="owner@example.com", 
            password="TestPassword123!", 
        ) 
        self.viewer = User.objects.create_user( 
            username="viewer", 
            email="viewer@example.com", 
            password="TestPassword123!", 
        ) 
        self.listed_friend = User.objects.create_user( 
            username="listed_friend", 
            email="listed_friend@example.com", 
            password="TestPassword123!", 
        ) 
        self.owner_profile = self.owner.profile 
        self.owner_friendship = Friendship.objects.create( 
            user=self.owner, 
            friend=self.listed_friend, 
        ) 
        self.profile_url = reverse( 
            "profile", 
            kwargs={"username": self.owner.username}, 
        ) 

    def test_owner_can_view_all_friend_lists(self): 
        self.client.force_login(self.owner) 
        response = self.client.get(self.profile_url) 
        self.assertEqual(response.status_code, 200) 
        self.assertTrue(response.context["can_view_friends"]) 
        self.assertTrue(response.context["can_view_close_friends"]) 
        self.assertTrue(response.context["can_view_top_friends"]) 

    def test_public_list_is_visible_to_authenticated_user(self): 
        self.owner_profile.top_friends_visibility = ( Profile.VisibilityChoices.PUBLIC ) 
        
        self.owner_profile.save( 
            update_fields=["top_friends_visibility"] 
        ) 
        
        self.owner_friendship.is_top_friend = True 
        
        self.owner_friendship.save( 
            update_fields=["is_top_friend"] 
        ) 
        
        self.client.force_login(self.viewer) 
        response = self.client.get(self.profile_url) 
        
        self.assertTrue(response.context["can_view_top_friends"]) 
        
        self.assertIn( 
            self.owner_friendship, 
            response.context["top_friends"], 
        ) 
        
    def test_friends_only_requires_existing_friendship(self): 
        
        self.owner_profile.friends_visibility = ( Profile.VisibilityChoices.FRIENDS ) 
        
        self.owner_profile.save( update_fields=["friends_visibility"] ) 
        
        self.client.force_login(self.viewer) 
        
        response = self.client.get(self.profile_url) 
        
        self.assertFalse(response.context["can_view_friends"]) 
        self.assertFalse(response.context["friends"].exists()) 
        
        Friendship.objects.create( 
            user=self.owner, 
            friend=self.viewer, 
        ) 
        
        response = self.client.get(self.profile_url) 
        
        
        self.assertTrue(response.context["can_view_friends"]) 
        
        self.assertIn( self.owner_friendship, response.context["friends"], ) 
        
    def test_close_friends_only_requires_owner_classification(self): 
        self.owner_profile.close_friends_visibility = ( Profile.VisibilityChoices.CLOSE_FRIENDS ) 
        
        self.owner_profile.save( update_fields=["close_friends_visibility"] ) 

        viewer_relationship = Friendship.objects.create( 
            user=self.owner, 
            friend=self.viewer, 
            is_close_friend=False, 
        ) 
        
        self.client.force_login(self.viewer) 
        
        response = self.client.get(self.profile_url) 
        
        self.assertFalse( response.context["can_view_close_friends"] ) 
        
        self.assertFalse( response.context["close_friends"].exists() ) 
        
        viewer_relationship.is_close_friend = True 
        viewer_relationship.save( update_fields=["is_close_friend"] ) 
        
        response = self.client.get(self.profile_url) 
        
        self.assertTrue( response.context["can_view_close_friends"] ) 
        
    def test_top_friends_only_requires_owner_classification(self): 
        self.owner_profile.top_friends_visibility = ( Profile.VisibilityChoices.TOP_FRIENDS ) 
        self.owner_profile.save( update_fields=["top_friends_visibility"] ) 
        
        viewer_relationship = Friendship.objects.create( 
            user=self.owner, 
            friend=self.viewer, 
            is_top_friend=False, 
        ) 
        
        self.client.force_login(self.viewer) 
        response = self.client.get(self.profile_url) 
        self.assertFalse( response.context["can_view_top_friends"] ) 
        self.assertFalse( response.context["top_friends"].exists() ) 
        viewer_relationship.is_top_friend = True 
        viewer_relationship.save( update_fields=["is_top_friend"] ) 
        response = self.client.get(self.profile_url) 
        self.assertTrue( response.context["can_view_top_friends"] ) 
        
    def test_only_me_hides_lists_from_other_users(self): 
        self.owner_profile.friends_visibility = ( Profile.VisibilityChoices.ONLY_ME ) 
        self.owner_profile.close_friends_visibility = ( Profile.VisibilityChoices.ONLY_ME ) 
        self.owner_profile.top_friends_visibility = ( Profile.VisibilityChoices.ONLY_ME ) 
        self.owner_profile.save( update_fields=[ "friends_visibility", "close_friends_visibility", "top_friends_visibility", ] ) 
        
        Friendship.objects.create( 
            user=self.owner, 
            friend=self.viewer, 
            is_close_friend=True, 
            is_top_friend=True, 
        ) 
        
        self.client.force_login(self.viewer) 
        response = self.client.get(self.profile_url) 
        self.assertFalse(response.context["can_view_friends"]) 
        self.assertFalse( response.context["can_view_close_friends"] ) 
        self.assertFalse( response.context["can_view_top_friends"] ) 
        self.assertFalse(response.context["friends"].exists()) 
        self.assertFalse( response.context["close_friends"].exists() ) 
        self.assertFalse( response.context["top_friends"].exists() ) 