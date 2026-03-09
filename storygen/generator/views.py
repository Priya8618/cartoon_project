import os
import uuid
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .forms import ImageStoryForm
from .models import ImageStory


# ==============================
# HOME PAGE — Upload Form
# ==============================

def home(request):
    """Render the home page with the image upload form."""
    form = ImageStoryForm()
    return render(request, 'generator/home.html', {'form': form})


# ==============================
# CARTOON IMAGE CONVERSION
# ==============================

def make_cartoon(image_path, output_path):
    """Convert a real image into a cartoon-style image using Pillow."""
    from PIL import Image, ImageFilter, ImageOps, ImageEnhance

    img = Image.open(image_path).convert('RGB')

    # Step 1: Reduce the image size for faster processing, then scale back
    small = img.resize((img.width // 2, img.height // 2))
    small = small.resize(img.size, Image.NEAREST)

    # Step 2: Reduce number of colors (posterize effect)
    posterized = ImageOps.posterize(small, 4)

    # Step 3: Boost color saturation for a vibrant cartoon look
    enhancer = ImageEnhance.Color(posterized)
    vibrant = enhancer.enhance(1.8)

    # Step 4: Increase brightness slightly
    bright_enhancer = ImageEnhance.Brightness(vibrant)
    bright = bright_enhancer.enhance(1.1)

    # Step 5: Smooth the image for that flat cartoon feel
    cartoon = bright.filter(ImageFilter.SMOOTH_MORE)
    cartoon = cartoon.filter(ImageFilter.SMOOTH_MORE)

    cartoon.save(output_path, 'PNG')
    return output_path


# ==============================
# VOICE-OVER GENERATION (gTTS)
# ==============================

def generate_voice(story_text, language, output_path):
    """Generate a voice-over MP3 from the story text using gTTS."""
    from gtts import gTTS

    lang_code_map = {
        'english': 'en',
        'hindi': 'hi',
        'kannada': 'kn',
        'tamil': 'ta',
        'telugu': 'te',
    }
    lang_code = lang_code_map.get(language, 'en')

    tts = gTTS(text=story_text, lang=lang_code, slow=False)
    tts.save(output_path)
    return output_path


# ==============================
# IMAGE ANALYSIS — Detect what is in the image
# ==============================

def analyze_image(image_path):
    """Analyze the image to detect dominant colors, brightness, and theme."""
    from PIL import Image

    img = Image.open(image_path).convert('RGB')
    img_small = img.resize((100, 100))
    pixels = list(img_small.getdata())

    color_counts = {
        'red': 0, 'orange': 0, 'yellow': 0, 'green': 0,
        'blue': 0, 'purple': 0, 'pink': 0, 'brown': 0,
        'white': 0, 'black': 0, 'gray': 0, 'skin': 0,
    }

    total_brightness = 0

    for r, g, b in pixels:
        brightness = (r + g + b) / 3
        total_brightness += brightness

        if r > 180 and g > 180 and b > 180:
            color_counts['white'] += 1
        elif r < 50 and g < 50 and b < 50:
            color_counts['black'] += 1
        elif abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
            color_counts['gray'] += 1
        elif r > 150 and g > 100 and b > 80 and r > b and g > b * 0.6:
            color_counts['skin'] += 1
        elif r > 180 and g < 100 and b < 100:
            color_counts['red'] += 1
        elif r > 180 and g > 100 and g < 180 and b < 100:
            color_counts['orange'] += 1
        elif r > 180 and g > 180 and b < 100:
            color_counts['yellow'] += 1
        elif g > 120 and r < 150 and b < 150 and g > r and g > b:
            color_counts['green'] += 1
        elif b > 120 and r < 150 and g < 180 and b > r:
            color_counts['blue'] += 1
        elif r > 100 and b > 100 and g < 100:
            color_counts['purple'] += 1
        elif r > 180 and b > 100 and g < 150:
            color_counts['pink'] += 1
        elif r > 100 and g > 50 and g < 120 and b < 80:
            color_counts['brown'] += 1

    avg_brightness = total_brightness / len(pixels)

    meaningful_colors = {k: v for k, v in color_counts.items()
                         if k not in ('white', 'black', 'gray') and v > 0}
    sorted_colors = sorted(meaningful_colors.items(), key=lambda x: x[1], reverse=True)
    top_colors = [c[0] for c in sorted_colors[:3]]

    has_person = color_counts['skin'] > 500
    is_bright = avg_brightness > 140
    is_dark = avg_brightness < 80

    theme = 'general'
    if 'green' in top_colors and 'brown' in top_colors:
        theme = 'nature'
    elif 'green' in top_colors and 'blue' in top_colors:
        theme = 'nature'
    elif 'blue' in top_colors and color_counts['blue'] > 2000:
        theme = 'ocean'
    elif 'orange' in top_colors and 'yellow' in top_colors:
        theme = 'sunset'
    elif 'red' in top_colors and 'yellow' in top_colors:
        theme = 'festival'
    elif is_dark and 'blue' in top_colors:
        theme = 'night'
    elif 'green' in top_colors:
        theme = 'garden'
    elif has_person:
        theme = 'adventure'
    elif 'pink' in top_colors or 'purple' in top_colors:
        theme = 'magical'
    elif 'yellow' in top_colors and is_bright:
        theme = 'sunny'
    elif 'brown' in top_colors:
        theme = 'earth'
    elif 'red' in top_colors:
        theme = 'celebration'
    elif is_bright:
        theme = 'happy'

    return {
        'theme': theme,
        'top_colors': top_colors,
        'brightness': 'bright' if is_bright else ('dark' if is_dark else 'warm'),
        'has_person': has_person,
    }


# ==============================
# STORY GENERATOR — Based on image analysis (with moral)
# ==============================

def generate_local_story(image_path, image_name):
    """Generate a fun cartoon story with a moral based on the uploaded image."""

    try:
        info = analyze_image(image_path)
        theme = info['theme']
        colors = info['top_colors']
    except Exception:
        theme = 'general'
        colors = []

    color_words = {
        'red': 'fiery red', 'orange': 'bright orange', 'yellow': 'sunny yellow',
        'green': 'lush green', 'blue': 'sparkling blue', 'purple': 'magical purple',
        'pink': 'lovely pink', 'brown': 'warm brown', 'skin': 'warm',
    }
    color_desc = ' and '.join([color_words.get(c, c) for c in colors[:2]]) if colors else 'colorful'

    # Each entry is (story, moral)
    stories = {
        'nature': [
            (
                f"In a beautiful {color_desc} forest, the trees danced and the flowers sang happy songs! "
                f"Whoosh! A little squirrel wearing a tiny hat swung from branch to branch, collecting "
                f"sparkling acorns. It noticed a baby bird that had fallen from its nest. "
                f"Without thinking twice, the squirrel gently carried the baby bird back to its home. "
                f"Zoom! All the forest animals cheered and the rainbow appeared to celebrate!",
                "Always help others when they are in need. A kind heart makes the world a beautiful place."
            ),
            (
                f"Deep in a {color_desc} meadow, butterflies of every color played a game of tag! "
                f"Splash! A little stream gurgled as tiny fish jumped over stones. "
                f"One day, a strong wind blew and knocked down many flowers. "
                f"All the animals worked together to plant new seeds and water them with care. "
                f"Soon the meadow was more beautiful than ever before!",
                "When we work together, we can overcome any challenge. Teamwork makes everything better."
            ),
        ],
        'ocean': [
            (
                f"Under the {color_desc} ocean waves, a brave little fish named Bubbles "
                f"discovered a beautiful coral reef that was losing its colors. Splash! "
                f"Bubbles asked all the sea creatures for help. The octopus cleaned the water, "
                f"the turtles planted new seaweed, and the dolphins sang encouraging songs. "
                f"Zoom! Together they made the reef sparkle with all the colors of the rainbow!",
                "Taking care of nature is everyone's responsibility. When we protect our environment, it rewards us with beauty."
            ),
            (
                f"By the {color_desc} seashore, a little crab found a shiny pearl! "
                f"Instead of keeping it, the crab shared it with a lonely starfish. "
                f"Whoosh! The starfish was so happy that it started glowing with joy! "
                f"Other sea creatures saw this and started sharing too. "
                f"Splash! Soon the whole ocean was lit up with the glow of kindness!",
                "Sharing brings more joy than keeping things to yourself. Happiness grows when you share it."
            ),
        ],
        'sunset': [
            (
                f"As the {color_desc} sun painted the sky, a little cloud named Fluffy felt sad "
                f"because it could not shine like the sun. Whoosh! The wise old moon appeared and said, "
                f"You bring rain that makes flowers grow, that is your special power! "
                f"Fluffy smiled and made the most gentle rain, and a beautiful rainbow appeared. "
                f"Zoom! Everyone cheered for Fluffy, the most special cloud in the sky!",
                "Everyone has their own unique talent. Never compare yourself to others, because you are special in your own way."
            ),
        ],
        'garden': [
            (
                f"In a {color_desc} garden, a tiny seed felt scared to grow because the world seemed so big. "
                f"Whoosh! A wise sunflower leaned down and said, Do not be afraid, just be brave one day at a time! "
                f"The little seed pushed through the soil bit by bit. Zoom! Days passed and it grew into "
                f"the most beautiful flower in the garden! Splash! All the butterflies came to celebrate! "
                f"The little flower realized that being brave was worth it!",
                "Courage starts with one small step. Even the biggest journeys begin with believing in yourself."
            ),
            (
                f"In a wonderful {color_desc} garden, a tiny caterpillar dreamed of flying! "
                f"All the other bugs laughed and said, You will never fly! "
                f"But the caterpillar did not give up. Whoosh! It worked hard, ate healthy leaves, "
                f"and spun a cozy cocoon. Zoom! Days later, out came the most gorgeous butterfly "
                f"with wings of every color! Everyone was amazed!",
                "Never let anyone tell you that you cannot achieve your dreams. Hard work and patience always pay off."
            ),
        ],
        'night': [
            (
                f"When the {color_desc} night sky sparkled, a little star named Twinkle felt too small "
                f"compared to the big bright stars. Whoosh! But one night, a lost little owl could not "
                f"find its way home. Twinkle shone as bright as it could to guide the owl. "
                f"Zoom! The owl found its way! All the big stars cheered for Twinkle. "
                f"From that night on, Twinkle was known as the most helpful star in the sky!",
                "No matter how small you are, you can make a big difference. It is not your size that matters, but your heart."
            ),
        ],
        'festival': [
            (
                f"In a town full of {color_desc} decorations, the festival was about to begin! "
                f"But the town baker had accidentally burned all the cakes! Whoosh! Everyone was sad. "
                f"Then all the children came together. Each one brought something from home. "
                f"Zoom! Together they made the most delicious cake the town had ever tasted! "
                f"The festival was saved and everyone danced with joy!",
                "When things go wrong, do not give up. Working together with a positive attitude can turn any problem into a celebration."
            ),
        ],
        'adventure': [
            (
                f"One {color_desc} morning, a brave young explorer set off to find the legendary "
                f"Friendship Tree. Whoosh! Along the way, the explorer met a scared rabbit, a lost turtle, "
                f"and a shy fox. Instead of rushing ahead, the explorer helped each one. "
                f"Zoom! When they finally reached the Friendship Tree together, it bloomed with golden flowers! "
                f"The tree only bloomed for those who helped others on their journey!",
                "The journey matters more than the destination. True success comes from the kindness we show along the way."
            ),
            (
                f"A curious young hero found a {color_desc} map leading to a mountain of wishes! "
                f"Whoosh! On the way, they met a crying puppy who had lost its toy. "
                f"The hero stopped the adventure to help find the toy. Zoom! "
                f"When the toy was found, the puppy was so happy that it led the hero to a shortcut! "
                f"Together they reached the mountain and wished for happiness for everyone!",
                "Helping others is never a waste of time. The kindness you give always comes back to you in unexpected ways."
            ),
        ],
        'magical': [
            (
                f"In a {color_desc} world of pure magic, a young wizard could not get any spell right! "
                f"Every spell went hilariously wrong. Whoosh! But the wizard never gave up and kept practicing. "
                f"One day, when a storm threatened the village, the wizard tried their hardest. "
                f"Zoom! The spell worked perfectly and created a magical shield! "
                f"The whole village cheered for the wizard who never stopped trying!",
                "Practice makes perfect. Do not be afraid of making mistakes, because each mistake teaches you something new."
            ),
        ],
        'sunny': [
            (
                f"On a beautiful {color_desc} sunny day, a little bunny wanted to grow the biggest carrot! "
                f"Whoosh! It watered the seed every morning and sang songs to it every evening. "
                f"Other animals said it was silly, but the bunny kept going. Zoom! "
                f"Weeks later, the most enormous, sparkly carrot popped out of the ground! "
                f"Splash! The bunny shared it with everyone and they had the best feast ever!",
                "Patience and dedication always bring great results. When you put love into your work, wonderful things happen."
            ),
        ],
        'celebration': [
            (
                f"The {color_desc} day was extra special, it was Kindness Day! "
                f"Whoosh! A little puppy decided to do something nice for every animal in town. "
                f"It brought flowers to the grumpy cat, shared bones with the shy hamster, "
                f"and sang songs for the lonely parrot. Zoom! By evening, every animal was smiling! "
                f"The whole town lit up with colorful lanterns to celebrate!",
                "One act of kindness can create a chain reaction. Be the reason someone smiles today."
            ),
        ],
        'earth': [
            (
                f"In a land of {color_desc} mountains, a little fox was the smallest in the family. "
                f"Whoosh! One day a big rockslide blocked the river. None of the big animals could fix it. "
                f"But the little fox noticed a small hole and dug through it carefully. "
                f"Zoom! The water flowed again! Splash! The whole valley was saved! "
                f"Everyone lifted the little fox on their shoulders and cheered!",
                "Even the smallest person can make the biggest difference. Never underestimate yourself."
            ),
        ],
        'happy': [
            (
                f"It was the most {color_desc} wonderful day in the happiest town ever! "
                f"But one little bird had a broken wing and felt left out. "
                f"Whoosh! All the other birds took turns bringing food and telling stories. "
                f"They made a tiny colorful wheelchair so the bird could join the games! "
                f"Zoom! The little bird won the singing contest and everyone cheered!",
                "True friends include everyone. The best kind of happiness is the one you share with others."
            ),
        ],
    }

    theme_stories = stories.get(theme, [])

    if not theme_stories:
        theme_stories = [
            (
                f"In a {color_desc} magical world, a curious little hero discovered a beautiful "
                f"garden where every flower told a different story. Whoosh! One flower was wilting "
                f"because nobody listened to its story. The hero sat down and listened carefully. "
                f"Zoom! The flower bloomed brighter than ever! Soon all the heroes friends came "
                f"to listen to the other flowers too, and the garden became the happiest place!",
                "Listening is one of the greatest gifts you can give someone. Everyone has a story worth hearing."
            ),
        ]

    story, moral = random.choice(theme_stories)
    return story, moral


# ==============================
# GENERATE STORY — with OpenAI (or fallback to image-based local)
# ==============================

def generate_story(request):
    """Handle image upload, generate story, translate, cartoonify, and add voice."""

    if request.method == 'POST':
        form = ImageStoryForm(request.POST, request.FILES)

        if form.is_valid():
            image_story = form.save(commit=False)
            language = form.cleaned_data['language']
            image_name = request.FILES['image'].name

            # Save now so image file gets written to disk
            image_story.save()
            image_path = image_story.image.path

            # --- Step 1: Generate a cartoon story ---
            story_text = None
            moral_text = None

            api_key = getattr(settings, 'OPENAI_API_KEY', 'your-api-key-here')
            if api_key and api_key != 'your-api-key-here':
                try:
                    import openai
                    openai.api_key = api_key

                    prompt = (
                        f"You are a creative children's story writer. "
                        f"Write a short, fun, cartoon-style story for children (5-8 years old) "
                        f"inspired by an image called '{image_name}'. "
                        f"The story should be 4-5 sentences long, colorful, imaginative, "
                        f"and use simple words. Add fun sounds like 'Whoosh!', 'Splash!', or 'Zoom!'. "
                        f"At the end, add a line starting with 'Moral:' followed by a one-line moral lesson."
                    )

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a fun cartoon story writer for kids."},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=400,
                        temperature=0.9,
                    )

                    full_text = response['choices'][0]['message']['content'].strip()

                    # Split story and moral
                    if 'Moral:' in full_text:
                        parts = full_text.split('Moral:', 1)
                        story_text = parts[0].strip()
                        moral_text = parts[1].strip()
                    else:
                        story_text = full_text
                        moral_text = "Every adventure teaches us something new. Be kind, be brave, and always be curious!"
                except Exception:
                    story_text = None
                    moral_text = None

            # Fallback: generate story based on actual image analysis
            if not story_text:
                story_text, moral_text = generate_local_story(image_path, image_name)

            # --- Step 2: Translate story if language is not English ---
            if language != 'english':
                try:
                    from deep_translator import GoogleTranslator
                    lang_code_map = {
                        'hindi': 'hi',
                        'kannada': 'kn',
                        'tamil': 'ta',
                        'telugu': 'te',
                    }
                    lang_code = lang_code_map.get(language, 'en')
                    translator = GoogleTranslator(source='auto', target=lang_code)
                    translated_story = translator.translate(story_text)
                    translated_moral = translator.translate(moral_text)
                    if translated_story:
                        story_text = translated_story
                    if translated_moral:
                        moral_text = translated_moral
                except Exception:
                    pass

            # Combine story + moral for saving
            image_story.story = story_text + "\n\n---MORAL---\n" + moral_text

            # --- Step 3: Convert image to cartoon style ---
            try:
                unique_name = f"cartoon_{uuid.uuid4().hex[:8]}.png"
                cartoon_dir = os.path.join(settings.MEDIA_ROOT, 'cartoons')
                os.makedirs(cartoon_dir, exist_ok=True)
                cartoon_path = os.path.join(cartoon_dir, unique_name)
                make_cartoon(image_path, cartoon_path)
                image_story.cartoon_image = f"cartoons/{unique_name}"
            except Exception:
                pass

            # --- Step 4: Generate voice-over (story + moral) ---
            try:
                full_voice_text = story_text + ". Moral of the story: " + moral_text
                unique_audio = f"story_{uuid.uuid4().hex[:8]}.mp3"
                audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
                os.makedirs(audio_dir, exist_ok=True)
                audio_path = os.path.join(audio_dir, unique_audio)
                generate_voice(full_voice_text, language, audio_path)
                image_story.audio = f"audio/{unique_audio}"
            except Exception:
                pass

            # --- Step 5: Final save ---
            image_story.save()

            return redirect('result', pk=image_story.pk)

    return redirect('home')


# ==============================
# RESULT PAGE — Display Story
# ==============================

def result(request, pk):
    """Display the generated story alongside the uploaded image."""
    image_story = get_object_or_404(ImageStory, pk=pk)

    # Split story and moral for display
    story_text = image_story.story
    moral_text = ""

    if "---MORAL---" in story_text:
        parts = story_text.split("---MORAL---", 1)
        story_text = parts[0].strip()
        moral_text = parts[1].strip()

    context = {
        'story': image_story,
        'story_text': story_text,
        'moral_text': moral_text,
    }
    return render(request, 'generator/result.html', context)
