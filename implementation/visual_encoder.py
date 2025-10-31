"""
HVATP Visual Encoder
Generates JAB Code-based color QR codes with advanced error correction
"""

import numpy as np
import cv2
from typing import Tuple, List
from enum import Enum
from reedsolo import RSCodec


class EncodingMode(Enum):
    """Visual encoding modes with different color depths"""
    HIGH_DENSITY = (8, 3)  # 8 colors, 3 bits/module
    BALANCED = (4, 2)       # 4 colors, 2 bits/module
    ROBUST = (2, 1)         # B&W, 1 bit/module
    
    def __init__(self, colors, bits_per_module):
        self.colors = colors
        self.bits_per_module = bits_per_module


class VisualEncoder:
    """
    Encodes data into JAB Code-like colored 2D barcodes
    """
    
    def __init__(self, 
                 mode: EncodingMode = EncodingMode.BALANCED,
                 module_count: int = 200,
                 error_correction_level: float = 0.35):
        """
        Args:
            mode: Encoding mode (color depth)
            module_count: Number of modules per side (square)
            error_correction_level: Fraction of data to use for RS parity (0.25-0.50)
        """
        self.mode = mode
        self.module_count = module_count
        self.ecc_level = error_correction_level
        
        # Reed-Solomon codec
        total_symbols = self._calculate_total_symbols()
        parity_symbols = int(total_symbols * error_correction_level)
        self.rs_codec = RSCodec(parity_symbols)
        
        # Color palette for different modes
        self.color_palettes = {
            EncodingMode.HIGH_DENSITY: self._generate_8_color_palette(),
            EncodingMode.BALANCED: self._generate_4_color_palette(),
            EncodingMode.ROBUST: self._generate_2_color_palette()
        }
        
    def _generate_8_color_palette(self) -> np.ndarray:
        """8-color palette optimized for smartphone cameras"""
        return np.array([
            [0, 0, 0],       # Black
            [255, 255, 255], # White
            [255, 0, 0],     # Red
            [0, 255, 0],     # Green
            [0, 0, 255],     # Blue
            [255, 255, 0],   # Yellow
            [255, 0, 255],   # Magenta
            [0, 255, 255],   # Cyan
        ], dtype=np.uint8)
        
    def _generate_4_color_palette(self) -> np.ndarray:
        """4-color palette with high contrast"""
        return np.array([
            [0, 0, 0],       # Black
            [255, 255, 255], # White
            [255, 0, 0],     # Red
            [0, 0, 255],     # Blue
        ], dtype=np.uint8)
        
    def _generate_2_color_palette(self) -> np.ndarray:
        """Standard B&W palette"""
        return np.array([
            [0, 0, 0],       # Black
            [255, 255, 255], # White
        ], dtype=np.uint8)
        
    def _calculate_total_symbols(self) -> int:
        """Calculate total data symbols available"""
        # Reserve space for finder patterns, metadata
        reserved_modules = 100  # Corners, timing, alignment
        data_modules = self.module_count ** 2 - reserved_modules
        
        # Convert modules to bytes
        bits = data_modules * self.mode.bits_per_module
        symbols = bits // 8
        
        return symbols
        
    def _add_finder_patterns(self, frame: np.ndarray) -> np.ndarray:
        """Add corner finder patterns (similar to QR codes)"""
        pattern_size = 10
        white = self.color_palettes[self.mode][1]
        black = self.color_palettes[self.mode][0]
        
        # Create finder pattern (7x7 with border)
        finder = np.zeros((pattern_size, pattern_size, 3), dtype=np.uint8)
        finder[:, :] = white
        finder[1:9, 1:9] = black
        finder[2:8, 2:8] = white
        finder[3:7, 3:7] = black
        
        # Top-left
        frame[0:pattern_size, 0:pattern_size] = finder
        
        # Top-right
        frame[0:pattern_size, -pattern_size:] = finder
        
        # Bottom-left
        frame[-pattern_size:, 0:pattern_size] = finder
        
        # Center (for large codes)
        if self.module_count > 150:
            center = self.module_count // 2
            offset = pattern_size // 2
            frame[center-offset:center+offset, center-offset:center+offset] = finder[:pattern_size//2, :pattern_size//2]
        
        return frame
        
    def _add_timing_patterns(self, frame: np.ndarray) -> np.ndarray:
        """Add alternating timing patterns"""
        white = self.color_palettes[self.mode][1]
        black = self.color_palettes[self.mode][0]
        
        # Horizontal timing (row 6)
        for i in range(10, self.module_count - 10):
            color = white if i % 2 == 0 else black
            frame[6, i] = color
            
        # Vertical timing (column 6)
        for i in range(10, self.module_count - 10):
            color = white if i % 2 == 0 else black
            frame[i, 6] = color
            
        return frame
        
    def _encode_metadata(self, frame_id: int, total_frames: int, data_length: int) -> bytes:
        """Encode frame metadata"""
        metadata = bytearray(8)
        metadata[0:3] = frame_id.to_bytes(3, 'big')  # 24-bit frame ID
        metadata[3:5] = total_frames.to_bytes(2, 'big')  # 16-bit total
        metadata[5:7] = data_length.to_bytes(2, 'big')  # 16-bit length
        
        # Checksum
        checksum = sum(metadata) & 0xFFFF
        metadata[7:9] = checksum.to_bytes(2, 'big')
        
        return bytes(metadata)
        
    def _data_to_modules(self, data: bytes) -> np.ndarray:
        """Convert byte data to color module values"""
        bits_per_module = self.mode.bits_per_module
        module_values = []
        
        bit_string = ''.join(format(byte, '08b') for byte in data)
        
        # Group bits by module size
        for i in range(0, len(bit_string), bits_per_module):
            chunk = bit_string[i:i + bits_per_module]
            if len(chunk) == bits_per_module:
                value = int(chunk, 2)
                module_values.append(value)
                
        return np.array(module_values, dtype=np.uint8)
        
    def encode_frame(self, 
                     data: bytes, 
                     frame_id: int = 0, 
                     total_frames: int = 1) -> np.ndarray:
        """
        Encode data into a single visual frame
        
        Args:
            data: Raw data to encode (will be truncated if too large)
            frame_id: Sequential frame number
            total_frames: Total number of frames in transmission
            
        Returns:
            RGB image as numpy array (module_count x module_count x 3)
        """
        # Calculate capacity
        total_symbols = self._calculate_total_symbols()
        data_symbols = total_symbols - self.rs_codec.nsym  # Subtract parity
        
        # Truncate or pad data
        if len(data) > data_symbols:
            data = data[:data_symbols]
        else:
            data = data + b'\x00' * (data_symbols - len(data))
            
        # Add Reed-Solomon error correction
        encoded_data = self.rs_codec.encode(data)
        
        # Convert to module values
        modules = self._data_to_modules(encoded_data)
        
        # Create frame image
        frame = np.zeros((self.module_count, self.module_count, 3), dtype=np.uint8)
        
        # Fill data area (skip reserved areas)
        palette = self.color_palettes[self.mode]
        module_idx = 0
        
        for y in range(self.module_count):
            for x in range(self.module_count):
                # Skip finder pattern areas
                if self._is_reserved_area(x, y):
                    continue
                    
                if module_idx < len(modules):
                    color_idx = modules[module_idx]
                    frame[y, x] = palette[color_idx]
                    module_idx += 1
                    
        # Add structural patterns
        frame = self._add_finder_patterns(frame)
        frame = self._add_timing_patterns(frame)
        
        # Add metadata in top-left reserved area (after finder pattern)
        metadata = self._encode_metadata(frame_id, total_frames, len(data))
        self._embed_metadata(frame, metadata)
        
        return frame
        
    def _is_reserved_area(self, x: int, y: int) -> bool:
        """Check if module position is reserved for patterns"""
        # Finder patterns (corners + center)
        if (x < 10 and y < 10) or \
           (x >= self.module_count - 10 and y < 10) or \
           (x < 10 and y >= self.module_count - 10):
            return True
            
        # Timing patterns
        if x == 6 or y == 6:
            return True
            
        # Metadata area
        if x < 20 and y >= 10 and y < 18:
            return True
            
        return False
        
    def _embed_metadata(self, frame: np.ndarray, metadata: bytes):
        """Embed metadata in reserved area with high redundancy"""
        # Use simple 8x repetition for critical metadata
        palette = self.color_palettes[self.mode]
        
        x_start, y_start = 10, 10
        for byte in metadata:
            for bit_pos in range(8):
                bit = (byte >> (7 - bit_pos)) & 1
                color = palette[bit]
                
                # Write bit multiple times for redundancy
                for dx in range(2):
                    for dy in range(2):
                        if x_start + dx < 20 and y_start + dy < 18:
                            frame[y_start + dy, x_start + dx] = color
                            
                x_start += 2
                if x_start >= 20:
                    x_start = 10
                    y_start += 2
                    
    def render_for_display(self, frame: np.ndarray, scale: int = 4) -> np.ndarray:
        """
        Scale up frame for display on screen
        
        Args:
            frame: Encoded frame (module_count x module_count x 3)
            scale: Pixel scale factor (larger = easier to decode)
            
        Returns:
            Upscaled image ready for display
        """
        height, width = frame.shape[:2]
        new_size = (width * scale, height * scale)
        
        # Nearest neighbor to preserve sharp module boundaries
        display_frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_NEAREST)
        
        return display_frame
        
        
class FrameSequenceEncoder:
    """Encodes large data into sequence of frames"""
    
    def __init__(self, encoder: VisualEncoder):
        self.encoder = encoder
        
    def encode_data(self, data: bytes) -> List[np.ndarray]:
        """
        Split data into multiple frames
        
        Returns:
            List of encoded frames
        """
        # Calculate per-frame capacity
        total_symbols = self.encoder._calculate_total_symbols()
        data_symbols = total_symbols - self.encoder.rs_codec.nsym
        
        frames = []
        total_frames = (len(data) + data_symbols - 1) // data_symbols
        
        for frame_id in range(total_frames):
            start = frame_id * data_symbols
            end = min(start + data_symbols, len(data))
            chunk = data[start:end]
            
            frame = self.encoder.encode_frame(chunk, frame_id, total_frames)
            frames.append(frame)
            
        return frames
        

# Example usage
if __name__ == "__main__":
    # Create encoder
    encoder = VisualEncoder(
        mode=EncodingMode.BALANCED,
        module_count=200,
        error_correction_level=0.35
    )
    
    # Encode test data
    test_data = b"Hello, HVATP! " * 100  # ~1.4 KB
    
    sequence_encoder = FrameSequenceEncoder(encoder)
    frames = sequence_encoder.encode_data(test_data)
    
    print(f"Encoded {len(test_data)} bytes into {len(frames)} frame(s)")
    print(f"Frame dimensions: {frames[0].shape}")
    
    # Display first frame
    display_frame = encoder.render_for_display(frames[0], scale=3)
    cv2.imwrite("test_frame.png", display_frame)
    print("Saved test frame to test_frame.png")
