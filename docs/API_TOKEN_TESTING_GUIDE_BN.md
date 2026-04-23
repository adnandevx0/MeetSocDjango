# MeetSoc API + Token Testing Guide (বাংলা)

Base URL (local): `http://127.0.0.1:6060/api/v1`

## 1) Token কিভাবে পাবেন

### Email/Password Login
- Endpoint: `POST /auth/login/`
- Body:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```
- Response এ `access` + `refresh` পাবেন।
- Protected API-তে header:
  - `Authorization: Bearer <access_token>`

### Refresh token
- Endpoint: `POST /auth/token/refresh/`
- Body:
```json
{"refresh": "<refresh_token>"}
```

### Logout (blacklist)
- Endpoint: `POST /auth/logout/`
- Body:
```json
{"refresh": "<refresh_token>"}
```

## 2) Google Login token কোথা থেকে নেবেন

Backend endpoint: `POST /auth/social/google/`

Backend expects:
- `id_token` **বা**
- `access_token`

Google Cloud Console steps:
1. [Google Cloud Console](https://console.cloud.google.com/) এ project
2. OAuth consent screen configure
3. OAuth Client তৈরি (Web/Android/iOS অনুযায়ী)
4. Frontend থেকে Google Sign-In করলে `id_token` বা access token পাবেন
5. ঐ token backend endpoint-এ পাঠাবেন

Example:
```json
{"id_token": "<google-id-token>"}
```

## 3) Facebook Login token কোথা থেকে নেবেন

Backend endpoint: `POST /auth/social/facebook/`

Facebook Developer steps:
1. [Meta for Developers](https://developers.facebook.com/) এ app তৈরি
2. Facebook Login product add
3. Frontend SDK দিয়ে login করলে `access_token` পাবেন
4. Backend-এ পাঠাবেন:
```json
{"access_token": "<facebook-access-token>"}
```

## 4) API ক্যাটাগরি অনুযায়ী টেস্ট

## Auth
- `POST /auth/register/`
- `POST /auth/login/`
- `POST /auth/logout/`
- `POST /auth/token/refresh/`
- `POST /auth/verify-email/send/`
- `POST /auth/verify-email/`
- `POST /auth/verify-phone/send/`
- `POST /auth/verify-phone/`
- `POST /auth/password/reset/`
- `POST /auth/password/reset/confirm/`
- `POST /auth/social/google/`
- `POST /auth/social/facebook/`

## Users/Friends
- `GET|PATCH /users/me/`
- `PATCH /users/me/avatar/`
- `PATCH /users/me/cover/`
- `GET /users/blocked/`
- `GET /users/people-you-may-know/`
- `GET /users/{user_id}/`
- `GET /users/{user_id}/posts/`
- `GET /users/{user_id}/photos/`
- `GET /users/{user_id}/friends/`
- `GET /users/{user_id}/followers/`
- `GET /users/{user_id}/following/`
- `POST /friends/request/{user_id}/`
- `POST /friends/accept/{user_id}/`
- `POST /friends/decline/{user_id}/`
- `DELETE /friends/unfriend/{user_id}/`
- `GET /friends/requests/`
- `GET /friends/suggestions/`
- `POST /friends/follow/{user_id}/`
- `DELETE /friends/unfollow/{user_id}/`
- `POST /users/block/{user_id}/`
- `DELETE /users/unblock/{user_id}/`

## Posts/Stories/Reactions/Comments
- `GET|POST /posts/`
- `GET|PUT|DELETE /posts/{post_id}/`
- `POST /posts/{post_id}/share/`
- `GET /posts/{post_id}/shares/`
- `POST /posts/{post_id}/view/`
- `POST /posts/{post_id}/save/`
- `GET|POST /stories/`
- `DELETE /stories/{story_id}/`
- `POST /stories/{story_id}/view/`
- `GET /stories/{story_id}/viewers/`
- `GET /stories/archive/`
- `POST /posts/{post_id}/react/`
- `GET /posts/{post_id}/reactions/`
- `POST /comments/{comment_id}/react/`
- `GET|POST /posts/{post_id}/comments/`
- `GET|PATCH|DELETE /comments/{comment_id}/`
- `GET|POST /comments/{comment_id}/replies/`

## Messages/Calls/Notifications
- `GET|POST /conversations/`
- `GET|DELETE /conversations/{conversation_id}/`
- `GET|POST /conversations/{conversation_id}/messages/`
- `GET|POST /conversations/{conversation_id}/members/`
- `DELETE /conversations/{conversation_id}/members/{user_id}/`
- `GET|PATCH|DELETE /messages/{message_id}/`
- `POST /messages/{message_id}/react/`
- `GET /users/online-status/`
- `POST /calls/initiate/`
- `POST /calls/{call_id}/accept/`
- `POST /calls/{call_id}/decline/`
- `POST /calls/{call_id}/end/`
- `GET /calls/history/`
- `GET /calls/ice-servers/`
- `GET /notifications/`
- `POST /notifications/mark-read/`
- `POST /notifications/{notification_id}/read/`
- `DELETE /notifications/{notification_id}/`
- `GET /notifications/unread-count/`
- `GET|PATCH /notifications/settings/`
- `POST /notifications/fcm-token/`

## Feed/Pages/Groups/Marketplace/Search/Watch/Memories
- `GET /feed/`
- `GET /feed/stories/`
- `POST /feed/hide/{post_id}/`
- `POST /feed/snooze/{user_id}/`
- `GET /feed/saved/`
- `GET|POST /pages/`
- `GET /pages/my/`
- `GET|PATCH|DELETE /pages/{slug}/`
- `POST /pages/{slug}/like/`
- `POST /pages/{slug}/follow/`
- `POST /pages/{slug}/unfollow/`
- `GET /pages/{slug}/posts/`
- `GET /pages/{slug}/followers/`
- `GET /pages/{slug}/admins/`
- `GET /pages/{slug}/insights/`
- `GET|POST /groups/`
- `GET /groups/my/`
- `GET|PATCH|DELETE /groups/{slug}/`
- `POST /groups/{slug}/join/`
- `POST /groups/{slug}/leave/`
- `GET /groups/{slug}/members/`
- `POST /groups/{slug}/invite/`
- `PATCH|DELETE /groups/{slug}/members/{uid}/`
- `GET /groups/{slug}/posts/`
- `GET /groups/{slug}/pending/`
- `POST /groups/{slug}/approve/{uid}/`
- `POST /groups/{slug}/ban/{uid}/`
- `GET|POST /marketplace/products/`
- `GET|PATCH|DELETE /marketplace/products/{product_id}/`
- `GET /search/`
- `GET|DELETE /search/recent/`
- `GET /search/trending/`
- `GET|POST /watch/videos/`
- `GET|PATCH|DELETE /watch/videos/{video_id}/`
- `GET /memories/`
- `GET /banned-accounts/`

## Blue Verification + Suspension (নতুন)
- `POST /verification/blue/apply/` (user আবেদন করবে)
- `GET /verification/blue/my-status/` (user badge status দেখবে)
- `GET /suspensions/my-status/` (নিজে suspended কিনা দেখবে)
- `GET|POST /admin/suspensions/` (admin suspension list/create)
- `POST /admin/suspensions/{suspension_id}/lift/` (admin suspension উঠাবে)

### Blue badge approval flow (Admin panel)
1. Admin -> `Blue Verification Requests`
2. request `approved` করুন
3. `valid_from` + `valid_until` দিন (যেমন: আজ থেকে 1 মাস)
4. ওই সময়ের মধ্যে user response-এ `has_blue_badge=true` দেখাবে
5. সময় পার হলে badge auto-inactive

## 5) Postman/Insomnia testing flow

1. প্রথমে `register` বা `login` hit করুন  
2. response থেকে `access` variable save করুন  
3. Collection-level Authorization: `Bearer {{access}}`  
4. create endpoints চালান (post/story/group/page/etc.)  
5. returned IDs env variable-এ সেভ করে detail endpoints টেস্ট করুন  

## 6) সাধারণ token সমস্যা ও সমাধান

- **401 Unauthorized**: access token missing/expired
- **403 Forbidden**: আছে token, কিন্তু role/ownership mismatch
- **400 Invalid Google/Facebook token**: frontend থেকে পাওয়া token ভুল audience/app id
- **CSRF/CORS issue**: `.env` এ allowed origins + trusted origins check করুন
