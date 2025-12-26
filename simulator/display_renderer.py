"""Renderer that converts displayio.Group hierarchy to pixel image."""

from PIL import Image, ImageDraw, ImageFont

from src.display_manager import DISPLAY_HEIGHT, DISPLAY_WIDTH


class DisplayRenderer:
    """Renders displayio.Group hierarchy to a pixel image."""

    def __init__(self):
        """Initialize the display renderer."""
        self._font_cache = {}
        self._base_font_size = 8
        self._render_scale = 1

    def _get_font(self, scale: int = 1) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Get a font at the specified scale.

        :param scale: Font scale factor
        :return: PIL ImageFont object
        """
        font_size = int(self._base_font_size * scale * self._render_scale)
        if font_size not in self._font_cache:
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/System/Library/Fonts/Monaco.ttf",
                "/System/Library/Fonts/Courier.ttc",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            ]
            font = None
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except OSError:
                    continue
            if font is None:
                font = ImageFont.load_default()
            self._font_cache[font_size] = font
        return self._font_cache[font_size]

    def _hex_to_rgb(self, color: int) -> tuple[int, int, int]:
        """Convert 0xRRGGBB color to RGB tuple.

        :param color: Color in 0xRRGGBB format
        :return: RGB tuple (r, g, b)
        """
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return (r, g, b)

    def _calculate_text_position(
        self, label, text_width: int, text_height: int
    ) -> tuple[int, int]:
        """Calculate the actual pixel position for a label based on anchor point.

        :param label: Label object with anchor_point and anchored_position
        :param text_width: Width of the text in pixels
        :param text_height: Height of the text in pixels
        :return: (x, y) position tuple
        """
        if hasattr(label, "anchored_position") and label.anchored_position:
            anchor_x, anchor_y = label.anchored_position
            anchor_point_x, anchor_point_y = label.anchor_point

            # Scale anchor positions to target resolution
            # text_width and text_height are already in target resolution
            scaled_anchor_x = anchor_x * self._render_scale
            scaled_anchor_y = anchor_y * self._render_scale

            # For x: 0.0 = left, 0.5 = center, 1.0 = right
            x = int(scaled_anchor_x - (anchor_point_x * text_width))
            # For y: 0.0 = top (no adjustment needed), 1.0 = bottom
            y = int(scaled_anchor_y - (anchor_point_y * text_height))
            return (x, y)
        else:
            return (
                int(label.x * self._render_scale),
                int(label.y * self._render_scale),
            )

    def _render_label(self, image: Image.Image, label) -> None:
        """Render a single label to the image.

        :param image: PIL Image to render to
        :param label: Label object to render
        """
        text = label.text if hasattr(label, "text") else ""
        if not text or not text.strip():
            return

        scale = label.scale if hasattr(label, "scale") else 1
        color = label.color if hasattr(label, "color") else 0xFFFFFF
        rgb_color = self._hex_to_rgb(color)

        font = self._get_font(scale)
        draw = ImageDraw.Draw(image)

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = int(bbox[2] - bbox[0])
        text_height = int(bbox[3] - bbox[1])

        x, y = self._calculate_text_position(label, text_width, text_height)

        # Convert from top-left (CircuitPython) to baseline (PIL)
        # textbbox returns bbox when baseline is at y=0, so bbox[1] is the top offset
        # (typically negative). To convert top-left y to baseline y, we subtract
        # bbox[1] (the negative top offset)
        if not (hasattr(label, "anchored_position") and label.anchored_position):
            y -= bbox[1]

        draw.text((x, y), text, font=font, fill=rgb_color)

    def _render_group(self, image: Image.Image, group) -> None:
        """Recursively render a group and all its children.

        :param image: PIL Image to render to
        :param group: Group object to render
        """
        if not group:
            return

        for item in group:
            if hasattr(item, "text"):
                self._render_label(image, item)
            elif hasattr(item, "__iter__") and not isinstance(item, str):
                self._render_group(image, item)

    def render(self, root_group, target_scale: int = 1) -> Image.Image:
        """Render the display root group to a pixel image.

        :param root_group: The root displayio.Group to render
        :param target_scale: Scale factor for rendering (1 = native size, 20 = 20x for window)
        :return: PIL Image of size (DISPLAY_WIDTH * target_scale, DISPLAY_HEIGHT * target_scale)
        """
        self._render_scale = target_scale
        width = DISPLAY_WIDTH * target_scale
        height = DISPLAY_HEIGHT * target_scale
        image = Image.new("RGB", (width, height), color=(0, 0, 0))
        if root_group:
            self._render_group(image, root_group)
        return image
