"""Tag matching configuration for PID Annotator."""


class TagMatchingConfig:
    """
    Configuration for customizable tag matching behavior.

    Attributes:
        preset: Preset name ('default', 'match_all', 'custom')
        min_parts: Minimum number of tag parts (default: 3)
        max_parts: Maximum number of tag parts (default: 5)
        separators: List of allowed separator characters (default: ['-', '.'])
        min_part_length: Minimum characters per part (default: 1)
        max_part_length: Maximum characters per part (default: 5)
        allow_partial_match: Allow partial tag matching (default: False)
        custom_regex: Optional custom regex pattern (overrides other settings)
    """

    def __init__(self, preset='default', min_parts=3, max_parts=5,
                 separators=None, min_part_length=1, max_part_length=5,
                 allow_partial_match=False, custom_regex=None):
        self.preset = preset
        self.min_parts = min_parts
        self.max_parts = max_parts
        self.separators = separators if separators is not None else ['-', '.']
        self.min_part_length = min_part_length
        self.max_part_length = max_part_length
        self.allow_partial_match = allow_partial_match
        self.custom_regex = custom_regex

    @classmethod
    def from_dict(cls, config_dict):
        """Create TagMatchingConfig from dictionary."""
        if not config_dict:
            return cls()  # Return default config

        return cls(
            preset=config_dict.get('preset', 'default'),
            min_parts=config_dict.get('min_parts', 3),
            max_parts=config_dict.get('max_parts', 5),
            separators=config_dict.get('separators', ['-', '.']),
            min_part_length=config_dict.get('min_part_length', 1),
            max_part_length=config_dict.get('max_part_length', 5),
            allow_partial_match=config_dict.get('allow_partial_match', False),
            custom_regex=config_dict.get('custom_regex', None)
        )

    def to_dict(self):
        """Convert TagMatchingConfig to dictionary."""
        return {
            'preset': self.preset,
            'min_parts': self.min_parts,
            'max_parts': self.max_parts,
            'separators': self.separators,
            'min_part_length': self.min_part_length,
            'max_part_length': self.max_part_length,
            'allow_partial_match': self.allow_partial_match,
            'custom_regex': self.custom_regex
        }

    @classmethod
    def get_default_preset(cls):
        """Get default preset configuration."""
        return cls(preset='default', min_parts=3, max_parts=5,
                   separators=['-', '.'], min_part_length=1, max_part_length=5,
                   allow_partial_match=False, custom_regex=None)

    @classmethod
    def get_match_all_preset(cls):
        """Get match-all preset configuration."""
        return cls(preset='match_all', min_parts=1, max_parts=10,
                   separators=['-', '.', '_', '/', ':'], min_part_length=1, max_part_length=20,
                   allow_partial_match=False, custom_regex=None)
