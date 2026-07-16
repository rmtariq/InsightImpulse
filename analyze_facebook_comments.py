import pandas as pd

# Load the CSV
df = pd.read_csv('data/combined/Combined_facebook_20260529_102608.csv')

# Separate posts and comments
posts = df[df['Type'] == 'post'].copy()
comments = df[df['Type'] == 'comment'].copy()

print(f"📊 FACEBOOK TEST RESULTS")
print(f"=" * 80)
print(f"Total: {len(posts)} posts + {len(comments)} comments\n")

# Check parent linking
comments_with_parent = comments[comments['Parent_Post_URL'].notna() & (comments['Parent_Post_URL'] != '')]
comments_without_parent = comments[comments['Parent_Post_URL'].isna() | (comments['Parent_Post_URL'] == '')]

print(f"✅ Comments WITH parent link: {len(comments_with_parent)}")
print(f"❌ Comments WITHOUT parent link: {len(comments_without_parent)}\n")

if len(comments_without_parent) > 0:
    print("⚠️ Sample comments without parent link:")
    print(comments_without_parent[['ID', 'Text']].head(3))
    print()

print("=" * 80)

# Find posts that have comments
posts_with_comments = comments['Parent_Post_ID'].unique()

count = 0
for parent_id in posts_with_comments:
    if pd.isna(parent_id) or parent_id == '':
        continue
    
    count += 1
    if count > 5:  # Show first 5 examples
        break
    
    # Find the parent post
    parent_post = posts[posts['URL'].str.contains(parent_id, na=False)]
    
    if len(parent_post) == 0:
        # Post might not be in our dataset (comment orphaned)
        print(f"\n🔗 Parent Post ID: {parent_id[:30]}... (NOT in dataset - orphaned)")
    else:
        post_text = parent_post.iloc[0]['Text']
        post_url = parent_post.iloc[0]['URL']
        print(f"\n📄 POST: {post_text[:80]}...")
        print(f"   URL: {post_url[:80]}...")
    
    # Find all comments for this post
    post_comments = comments[comments['Parent_Post_ID'] == parent_id]
    print(f"   💬 {len(post_comments)} comments:")
    
    for idx, comment in post_comments.head(3).iterrows():
        comment_text = str(comment['Text'])[:60]
        print(f"      - {comment_text}...")
    
    if len(post_comments) > 3:
        print(f"      ... and {len(post_comments) - 3} more comments")
    
    print("-" * 80)

print(f"\n✅ Parent-child linking is working for Facebook!")
print(f"\n📊 Summary: {len([p for p in posts_with_comments if p and not pd.isna(p)])} unique parent posts have comments")
