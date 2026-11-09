# Animated profile README assets

This guide documents the animated assets used in the `uzi-090` GitHub profile.

## Assets

- `pixel-room-uzair.gif` — animated pixel-room header.
- `discord-black-premium.svg` — compact animated Discord link button.

## Embed the Discord button

Keep a normal anchor around the image so the entire button opens the profile.

```html
<p align="center">
  <a href="https://discord.com/users/737953430051618839">
    <img src="./discord-black-premium.svg"
         alt="Open my Discord profile"
         width="286" />
  </a>
</p>
```

## Quality checklist

1. Check that the button is still legible against GitHub's light and dark themes.
2. Verify the icon, border and text stay inside the pill-shaped outline.
3. **Preview after upload:** open your GitHub profile README and check that the uploaded SVG button renders and its border animation plays. If the image is missing, check the `src` filename and path.
4. Confirm the Discord link opens the correct profile.
5. Use descriptive `alt` text; images may not load for every reader.
6. Prefer self-contained SVG animations rather than JavaScript for README images.
7. Keep the original GIF and SVG in the repository so local image paths keep working.

## Collaboration review

Thanks to @marinoo-utmsem3 for reviewing the guide and suggesting the post-upload SVG preview check (step 3 above).
