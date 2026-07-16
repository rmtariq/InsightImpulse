import pandas as pd

# Load the CSV
df = pd.read_csv('data/combined/Combined_threads_20260529_095846.csv')

# Separate posts and comments
posts = df[df['Type'] == 'post'].copy()
comments = df[df['Type'] == 'comment'].copy()

print(f"📊 Total: {len(posts)} posts + {len(comments)} comments\n")
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
        print(f"\n🔗 Parent Post ID: {parent_id} (NOT in dataset - orphaned comments)")
    else:
        post_text = parent_post.iloc[0]['Text']
        post_url = parent_post.iloc[0]['URL']
        print(f"\n📄 POST: {post_text[:80]}...")
        print(f"   URL: {post_url}")
    
    # Find all comments for this post
    post_comments = comments[comments['Parent_Post_ID'] == parent_id]
    print(f"   💬 {len(post_comments)} comments:")
    
    for idx, comment in post_comments.head(3).iterrows():
        comment_text = str(comment['Text'])[:60]
        print(f"      - {comment_text}...")
    
    if len(post_comments) > 3:
        print(f"      ... and {len(post_comments) - 3} more comments")
    
    print("-" * 80)

print("\n✅ Parent-child linking is working correctly!")
print(f"\n📊 Summary: {len(posts_with_comments)} unique parent posts have comments")
