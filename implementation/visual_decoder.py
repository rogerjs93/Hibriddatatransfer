"""
HVATP Visual Decoder
Decodes JAB Code-based color QR codes from camera input
"""

import numpy as np
import cv2
from typing import Optional, Tuple, List
from reedsolo import RSCodec
from dataclasses import dataclass


@dataclass
class DecodedFrame:
    """Container for decoded frame data"""
    frame_id: int
    total_frames: int
    data: bytes
    success: bool
    error_count: int = 0
    decode_time_ms: float = 0.0


class VisualDecoder:
    """
    Decodes JAB Code-like colored 2D barcodes from camera images
    """
    
    def __init__(self,
                 expected_module_count: int = 200,
                 error_correction_level: float = 0.35):
        """
        Args:
            expected_module_count: Expected modules per side
            error_correction_level: ECC level matching encoder
        """
        self.expected_module_count = expected_module_count
        self.ecc_level = error_correction_level
        
        # Reed-Solomon decoder
        total_symbols = self._calculate_total_symbols()
        parity_symbols = int(total_symbols * error_correction_level)
        self.rs_codec = RSCodec(parity_symbols)
        
        # Detection parameters
        self.finder_pattern_size = 10
        
        # Performance tracking
        self.frames_attempted = 0
        self.frames_successful = 0
        
    def _calculate_total_symbols(self) -> int:
        """Calculate total data symbols"""
        reserved_modules = 100
        data_modules = self.expected_module_count ** 2 - reserved_modules
        # Assume balanced mode (2 bits/module) for calculation
        bits = data_modules * 2
        symbols = bits // 8
        return symbols
        
    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocessing to improve detection"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Bilateral filter to reduce noise while preserving edges
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        return enhanced
        
    def _detect_finder_patterns(self, image: np.ndarray) -> List[Tuple[int, int]]:
        """
        Detect corner finder patterns
        
        Returns:
            List of (x, y) coordinates of finder pattern centers
        """
        # Use template matching for finder patterns
        # Create template (simplified - actual would be more complex)
        template = self._create_finder_template()
        
        # Multi-scale matching
        scales = [0.8, 1.0, 1.2]
        all_locations = []
        
        for scale in scales:
            h, w = template.shape
            scaled_template = cv2.resize(template, 
                                        (int(w * scale), int(h * scale)),
                                        interpolation=cv2.INTER_AREA)
            
            # Template matching
            result = cv2.matchTemplate(image, scaled_template, cv2.TM_CCOEFF_NORMED)
            
            # Find peaks
            threshold = 0.6
            locations = np.where(result >= threshold)
            
            for pt in zip(*locations[::-1]):
                all_locations.append((pt[0] + w//2, pt[1] + h//2))
                
        # Cluster nearby detections
        if len(all_locations) < 3:
            return []
            
        # Simple clustering: find 3-4 corners
        clustered = self._cluster_points(all_locations, min_distance=50)
        
        return clustered[:4]  # Max 4 corners
        
    def _create_finder_template(self) -> np.ndarray:
        """Create finder pattern template for matching"""
        size = self.finder_pattern_size
        template = np.ones((size, size), dtype=np.uint8) * 255
        
        # Black border
        template[1:size-1, 1:size-1] = 0
        
        # White middle
        template[2:size-2, 2:size-2] = 255
        
        # Black center
        template[3:size-3, 3:size-3] = 0
        
        return template
        
    def _cluster_points(self, points: List[Tuple[int, int]], min_distance: int) -> List[Tuple[int, int]]:
        """Cluster nearby points and return cluster centers"""
        if not points:
            return []
            
        clusters = []
        used = set()
        
        for i, pt1 in enumerate(points):
            if i in used:
                continue
                
            cluster = [pt1]
            used.add(i)
            
            for j, pt2 in enumerate(points):
                if j in used:
                    continue
                    
                dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                if dist < min_distance:
                    cluster.append(pt2)
                    used.add(j)
                    
            # Cluster center
            center_x = int(np.mean([p[0] for p in cluster]))
            center_y = int(np.mean([p[1] for p in cluster]))
            clusters.append((center_x, center_y))
            
        return clusters
        
    def _order_corners(self, corners: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Order corners as: top-left, top-right, bottom-right, bottom-left"""
        if len(corners) < 3:
            return corners
            
        # Find centroid
        cx = np.mean([c[0] for c in corners])
        cy = np.mean([c[1] for c in corners])
        
        # Compute angles from centroid
        angles = []
        for x, y in corners:
            angle = np.arctan2(y - cy, x - cx)
            angles.append(angle)
            
        # Sort by angle
        sorted_corners = [c for _, c in sorted(zip(angles, corners))]
        
        # Rotate so top-left is first
        # Top-left should have smallest sum of coordinates
        min_idx = np.argmin([c[0] + c[1] for c in sorted_corners])
        sorted_corners = sorted_corners[min_idx:] + sorted_corners[:min_idx]
        
        return sorted_corners
        
    def _perspective_transform(self, 
                              image: np.ndarray, 
                              corners: List[Tuple[int, int]]) -> Optional[np.ndarray]:
        """
        Apply perspective transform to get frontal view
        
        Returns:
            Warped image or None if transform fails
        """
        if len(corners) != 4:
            return None
            
        # Order corners
        corners = self._order_corners(corners)
        
        # Source points
        src_pts = np.array(corners, dtype=np.float32)
        
        # Destination points (square)
        size = self.expected_module_count * 4  # 4 pixels per module
        dst_pts = np.array([
            [0, 0],
            [size, 0],
            [size, size],
            [0, size]
        ], dtype=np.float32)
        
        # Compute perspective transform
        try:
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(image, matrix, (size, size))
            return warped
        except:
            return None
            
    def _extract_modules(self, 
                        warped_image: np.ndarray,
                        color_mode: int = 4) -> np.ndarray:
        """
        Extract individual module values from warped image
        
        Args:
            warped_image: Perspective-corrected image
            color_mode: Number of colors (2, 4, or 8)
            
        Returns:
            Array of module values
        """
        module_count = self.expected_module_count
        pixels_per_module = warped_image.shape[0] // module_count
        
        modules = []
        
        for y in range(module_count):
            for x in range(module_count):
                # Skip reserved areas
                if self._is_reserved_area(x, y):
                    continue
                    
                # Extract module region (center 60% to avoid border effects)
                y_start = y * pixels_per_module + pixels_per_module // 5
                y_end = (y + 1) * pixels_per_module - pixels_per_module // 5
                x_start = x * pixels_per_module + pixels_per_module // 5
                x_end = (x + 1) * pixels_per_module - pixels_per_module // 5
                
                module_region = warped_image[y_start:y_end, x_start:x_end]
                
                # Determine color
                if len(module_region.shape) == 3:
                    avg_color = np.mean(module_region, axis=(0, 1))
                    module_value = self._color_to_value(avg_color, color_mode)
                else:
                    avg_intensity = np.mean(module_region)
                    module_value = self._intensity_to_value(avg_intensity, color_mode)
                    
                modules.append(module_value)
                
        return np.array(modules, dtype=np.uint8)
        
    def _is_reserved_area(self, x: int, y: int) -> bool:
        """Check if module position is reserved"""
        # Same logic as encoder
        if (x < 10 and y < 10) or \
           (x >= self.expected_module_count - 10 and y < 10) or \
           (x < 10 and y >= self.expected_module_count - 10):
            return True
        if x == 6 or y == 6:
            return True
        if x < 20 and y >= 10 and y < 18:
            return True
        return False
        
    def _color_to_value(self, color: np.ndarray, color_mode: int) -> int:
        """Map RGB color to discrete value"""
        # Define palettes
        if color_mode == 2:
            # B&W
            threshold = 128
            return 1 if np.mean(color) > threshold else 0
            
        elif color_mode == 4:
            # 4-color palette
            palette = np.array([
                [0, 0, 0],       # Black
                [255, 255, 255], # White
                [255, 0, 0],     # Red
                [0, 0, 255],     # Blue
            ])
            
        elif color_mode == 8:
            # 8-color palette
            palette = np.array([
                [0, 0, 0], [255, 255, 255],
                [255, 0, 0], [0, 255, 0], [0, 0, 255],
                [255, 255, 0], [255, 0, 255], [0, 255, 255],
            ])
        else:
            return 0
            
        # Find closest palette color
        distances = np.sum((palette - color) ** 2, axis=1)
        return np.argmin(distances)
        
    def _intensity_to_value(self, intensity: float, color_mode: int) -> int:
        """Map grayscale intensity to discrete value"""
        # Simple threshold-based
        thresholds = {
            2: [128],
            4: [64, 128, 192],
            8: [32, 64, 96, 128, 160, 192, 224]
        }
        
        if color_mode not in thresholds:
            return 0
            
        for i, threshold in enumerate(thresholds[color_mode]):
            if intensity < threshold:
                return i
                
        return color_mode - 1
        
    def _modules_to_data(self, modules: np.ndarray, bits_per_module: int) -> bytes:
        """Convert module values back to bytes"""
        bits = []
        
        for module in modules:
            # Convert to binary
            module_bits = format(int(module), f'0{bits_per_module}b')
            bits.append(module_bits)
            
        # Combine into byte string
        bit_string = ''.join(bits)
        
        # Convert to bytes
        data = bytearray()
        for i in range(0, len(bit_string), 8):
            byte_bits = bit_string[i:i+8]
            if len(byte_bits) == 8:
                data.append(int(byte_bits, 2))
                
        return bytes(data)
        
    def decode_frame(self, 
                    camera_image: np.ndarray,
                    color_mode: int = 4) -> Optional[DecodedFrame]:
        """
        Decode a single frame from camera image
        
        Args:
            camera_image: Raw camera frame (BGR or grayscale)
            color_mode: Expected color depth (2, 4, or 8)
            
        Returns:
            DecodedFrame object or None if decoding fails
        """
        import time
        start_time = time.time()
        
        self.frames_attempted += 1
        
        # 1. Enhance image
        enhanced = self._enhance_image(camera_image)
        
        # 2. Detect finder patterns
        corners = self._detect_finder_patterns(enhanced)
        if len(corners) < 3:
            return None
            
        # 3. Perspective transform
        warped = self._perspective_transform(camera_image, corners)
        if warped is None:
            return None
            
        # 4. Extract modules
        modules = self._extract_modules(warped, color_mode)
        
        # 5. Convert to bytes
        bits_per_module = {2: 1, 4: 2, 8: 3}[color_mode]
        encoded_data = self._modules_to_data(modules, bits_per_module)
        
        # 6. Reed-Solomon decode
        try:
            decoded_data, corrected_errors = self.rs_codec.decode(encoded_data)
            error_count = len(corrected_errors) if isinstance(corrected_errors, list) else 0
        except:
            # Decoding failed
            return None
            
        # 7. Extract metadata (simplified - actual would parse from reserved area)
        # For now, assume metadata is prepended
        if len(decoded_data) < 8:
            return None
            
        frame_id = int.from_bytes(decoded_data[0:3], 'big')
        total_frames = int.from_bytes(decoded_data[3:5], 'big')
        data_length = int.from_bytes(decoded_data[5:7], 'big')
        
        # Extract actual data
        actual_data = decoded_data[8:8+data_length]
        
        decode_time = (time.time() - start_time) * 1000
        
        self.frames_successful += 1
        
        return DecodedFrame(
            frame_id=frame_id,
            total_frames=total_frames,
            data=actual_data,
            success=True,
            error_count=error_count,
            decode_time_ms=decode_time
        )
        
    def get_success_rate(self) -> float:
        """Get frame decode success rate"""
        if self.frames_attempted == 0:
            return 0.0
        return self.frames_successful / self.frames_attempted


# Example usage
if __name__ == "__main__":
    # Create decoder
    decoder = VisualDecoder(
        expected_module_count=200,
        error_correction_level=0.35
    )
    
    # Simulate decoding from camera
    # In real use, this would be a camera frame
    test_image = cv2.imread("test_frame.png")
    
    if test_image is not None:
        result = decoder.decode_frame(test_image, color_mode=4)
        
        if result and result.success:
            print(f"Successfully decoded frame {result.frame_id}/{result.total_frames}")
            print(f"Data length: {len(result.data)} bytes")
            print(f"Errors corrected: {result.error_count}")
            print(f"Decode time: {result.decode_time_ms:.1f} ms")
            print(f"Data preview: {result.data[:50]}...")
        else:
            print("Decoding failed")
            
        print(f"Overall success rate: {decoder.get_success_rate() * 100:.1f}%")
    else:
        print("Test image not found. Run visual_encoder.py first to generate test_frame.png")
