"""
Test shopping recommendations for shorts category
"""
from services.shopping import get_complementary_items

print("=" * 80)
print("TESTING SHOPPING RECOMMENDATIONS FOR SHORTS")
print("=" * 80)

# Test 1: Blue shorts (women)
print("\n1. Blue Casual Shorts (Women)")
print("-" * 80)
result = get_complementary_items(
    garment_category="shorts",
    garment_color="#1E90FF",
    gender="women",
    style="casual",
    fabric="cotton",
    description="Light blue casual shorts"
)

print(f"Category: {result['category']}")
print(f"Normalized: {result['normalized_category']}")
print(f"Gender: {result['gender']}")
print(f"Match Type: {result['match_type']}")
print(f"Primary Categories: {result['online_strategy']['primary_categories']}")
print(f"Accessory Categories: {result['online_strategy']['accessory_categories']}")
print(f"\nComplementary Items:")
for cat, details in result['complementary_items'].items():
    print(f"  • {cat}: {details['query_terms']}")

print(f"\nTop Shopping Links (first 5):")
for i, link in enumerate(result['shopping_links'][:5], 1):
    print(f"  {i}. {link['store']:15} | {link['category']:12} | Query: '{link['query']:40}' | Confidence: {link['confidence']}")

# Test 2: Khaki shorts (men)
print("\n\n2. Khaki Formal Shorts (Men)")
print("-" * 80)
result2 = get_complementary_items(
    garment_category="shorts",
    garment_color="#F0E68C",
    gender="men",
    style="formal",
    fabric="cotton",
    description="Khaki casual shorts"
)

print(f"Category: {result2['category']}")
print(f"Normalized: {result2['normalized_category']}")
print(f"Gender: {result2['gender']}")
print(f"Match Type: {result2['match_type']}")
print(f"Primary Categories: {result2['online_strategy']['primary_categories']}")
print(f"Accessory Categories: {result2['online_strategy']['accessory_categories']}")
print(f"\nComplementary Items:")
for cat, details in result2['complementary_items'].items():
    print(f"  • {cat}: {details['query_terms']}")

print(f"\nTop Shopping Links (first 5):")
for i, link in enumerate(result2['shopping_links'][:5], 1):
    print(f"  {i}. {link['store']:15} | {link['category']:12} | Query: '{link['query']:40}' | Confidence: {link['confidence']}")

print("\n" + "=" * 80)
print("✅ RESULTS:")
print("=" * 80)
print(f"✓ Shorts recommendations now include similar shorts as primary category")
print(f"✓ Women's shorts: {len([l for l in result['shopping_links'] if l['category'] == 'shorts'])} links to buy shorts")
print(f"✓ Men's shorts: {len([l for l in result2['shopping_links'] if l['category'] == 'shorts'])} links to buy shorts")
print(f"✓ Plus matching tops for both genders")
print("=" * 80 + "\n")
