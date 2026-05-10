import dearpygui.dearpygui as dpg


class ControlPanel:
    def __init__(self, params, state):
        self.params = params
        self.state = state
        self._closed = False

        dpg.create_context()
        dpg.create_viewport(title="Hex Tiles Controls", width=380, height=520)

        with dpg.window(label="Hex Tiling", tag="controls", width=360, height=480):
            dpg.add_text("Texture")
            dpg.add_text("", tag="texture_label")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Previous Texture", callback=self.previous_texture)
                dpg.add_button(label="Next Texture", callback=self.next_texture)
            dpg.add_separator()

            dpg.add_text("Tiling")
            dpg.add_combo(
                ("Hex blend", "Tri stochastic"),
                label="Mode",
                tag="tiling_mode",
                default_value="Hex blend",
                callback=self.set_tiling_mode,
            )
            dpg.add_slider_float(
                label="Tile Frequency",
                tag="tile_freq",
                default_value=params.tile_freq,
                min_value=0.15,
                max_value=4.0,
                callback=lambda _, value: setattr(params, "tile_freq", value),
            )
            dpg.add_slider_float(
                label="Hex Size",
                tag="hex_size",
                default_value=params.hex_size,
                min_value=16.0,
                max_value=180.0,
                callback=lambda _, value: setattr(params, "hex_size", value),
            )
            dpg.add_slider_float(
                label="Blend Sharpness",
                tag="blend_power",
                default_value=params.blend_power,
                min_value=0.3,
                max_value=8.0,
                callback=lambda _, value: setattr(params, "blend_power", value),
            )
            dpg.add_checkbox(
                label="Random Rotation",
                tag="rotate",
                default_value=params.rotate,
                callback=lambda _, value: setattr(params, "rotate", value),
            )
            dpg.add_checkbox(
                label="Random Mirror",
                tag="mirror",
                default_value=params.mirror,
                callback=lambda _, value: setattr(params, "mirror", value),
            )
            dpg.add_checkbox(
                label="Luminance Blend",
                tag="lum_blend",
                default_value=params.lum_blend,
                callback=lambda _, value: setattr(params, "lum_blend", value),
            )
            dpg.add_separator()

            dpg.add_text("Noisy Border Mask")
            dpg.add_checkbox(
                label="Enable Noise",
                tag="noise_blend",
                default_value=params.noise_blend,
                callback=lambda _, value: setattr(params, "noise_blend", value),
            )
            dpg.add_slider_float(
                label="Noise Strength",
                tag="noise_strength",
                default_value=params.noise_strength,
                min_value=0.0,
                max_value=1.0,
                callback=lambda _, value: setattr(params, "noise_strength", value),
            )
            dpg.add_slider_float(
                label="Noise Contrast",
                tag="noise_contrast",
                default_value=params.noise_contrast,
                min_value=0.1,
                max_value=5.0,
                callback=lambda _, value: setattr(params, "noise_contrast", value),
            )
            dpg.add_slider_float(
                label="Noise Scale",
                tag="noise_scale",
                default_value=params.noise_scale,
                min_value=0.005,
                max_value=0.12,
                callback=lambda _, value: setattr(params, "noise_scale", value),
            )
            dpg.add_separator()

            dpg.add_checkbox(
                label="Pause Animation",
                default_value=state["paused"],
                callback=lambda _, value: self.set_paused(value),
                tag="pause_checkbox",
            )
            with dpg.group(horizontal=True):
                dpg.add_button(label="Reset Defaults", callback=self.reset_defaults)
                dpg.add_button(label="Quit", callback=self.close)

        dpg.setup_dearpygui()
        dpg.show_viewport()
        self.update_labels()

    @property
    def should_close(self):
        return self._closed or not dpg.is_dearpygui_running()

    def render_frame(self):
        self.update_labels()
        dpg.render_dearpygui_frame()

    def update_labels(self):
        textures = self.state["atlas_textures"]
        total = len(textures) if textures else 1
        dpg.set_value("texture_label", f"{self.state['texture_index'] + 1} / {total}")

    def set_paused(self, value):
        self.state["paused"] = value

    def set_tiling_mode(self, _, value):
        self.params.tiling_mode = 1 if value == "Tri stochastic" else 0

    def next_texture(self, *_):
        self.state["request_texture_cycle"](1)

    def previous_texture(self, *_):
        self.state["request_texture_cycle"](-1)

    def reset_defaults(self, *_):
        defaults = type(self.params)()
        for field in self.params.__dataclass_fields__:
            if field != "t":
                setattr(self.params, field, getattr(defaults, field))

        dpg.set_value("tiling_mode", "Tri stochastic" if self.params.tiling_mode else "Hex blend")
        for field in (
            "tile_freq",
            "hex_size",
            "blend_power",
            "noise_strength",
            "noise_contrast",
            "noise_scale",
            "rotate",
            "mirror",
            "lum_blend",
            "noise_blend",
        ):
            dpg.set_value(field, getattr(self.params, field))

    def close(self, *_):
        self._closed = True

    def destroy(self):
        dpg.destroy_context()
