"""
HVATP Example: End-to-End File Transfer
Demonstrates complete workflow from encoding to decoding
"""

import numpy as np
import cv2
import time
from pathlib import Path

# Import our modules
from visual_encoder import VisualEncoder, EncodingMode, FrameSequenceEncoder
from visual_decoder import VisualDecoder
from audio_encoder import AudioEncoder, AudioPacketBuilder, ModulationType, PacketType


class HVATPSender:
    """Complete sender implementation"""
    
    def __init__(self,
                 visual_mode: EncodingMode = EncodingMode.BALANCED,
                 audio_modulation: ModulationType = ModulationType.QPSK,
                 display_scale: int = 3):
        """
        Initialize HVATP sender
        
        Args:
            visual_mode: Visual encoding mode
            audio_modulation: Audio modulation scheme
            display_scale: Pixel scale for display rendering
        """
        self.visual_encoder = VisualEncoder(
            mode=visual_mode,
            module_count=200,
            error_correction_level=0.35
        )
        
        self.audio_encoder = AudioEncoder(
            sample_rate=48000,
            num_subcarriers=48,
            modulation=audio_modulation
        )
        
        self.audio_builder = AudioPacketBuilder(self.audio_encoder)
        self.display_scale = display_scale
        
        # Stats
        self.frames_sent = 0
        self.bytes_sent = 0
        self.start_time = None
        
    def send_file(self, filepath: str, display_window: str = "HVATP Transfer"):
        """
        Send a file using HVATP protocol
        
        Args:
            filepath: Path to file to send
            display_window: OpenCV window name for display
        """
        print(f"📂 Loading file: {filepath}")
        with open(filepath, 'rb') as f:
            data = f.read()
        
        print(f"📊 File size: {len(data)} bytes ({len(data)/1024:.1f} KB)")
        
        # Encode into visual frames
        print("🎨 Encoding visual frames...")
        sequence_encoder = FrameSequenceEncoder(self.visual_encoder)
        visual_frames = sequence_encoder.encode_data(data)
        
        print(f"✅ Generated {len(visual_frames)} visual frames")
        
        # Create window
        cv2.namedWindow(display_window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(display_window, 800, 800)
        
        self.start_time = time.time()
        self.frames_sent = 0
        self.bytes_sent = 0
        
        # Display frames
        print("📺 Starting transmission...")
        for frame_id, frame in enumerate(visual_frames):
            # Render for display
            display_frame = self.visual_encoder.render_for_display(
                frame, scale=self.display_scale
            )
            
            # Show frame
            cv2.imshow(display_window, display_frame)
            
            # Generate accompanying audio packet (ACK request)
            audio_packet = self.audio_builder.build_ack_packet(
                frame_id=frame_id,
                ack_bitmap=0xFFFFFFFFFFFFFFFF  # Expecting all ACKs
            )
            
            # In real implementation: play audio_packet through speaker
            # For demo: just acknowledge packet was generated
            
            # Update stats
            self.frames_sent += 1
            frame_bytes = len(data) // len(visual_frames)
            self.bytes_sent += frame_bytes
            
            # Display progress
            elapsed = time.time() - self.start_time
            throughput = self.bytes_sent / elapsed if elapsed > 0 else 0
            
            print(f"Frame {frame_id+1}/{len(visual_frames)} | "
                  f"Throughput: {throughput/1024:.1f} KB/s | "
                  f"Elapsed: {elapsed:.1f}s", end='\r')
            
            # Wait for frame duration (30 fps = 33.3ms)
            key = cv2.waitKey(33)
            if key == ord('q'):
                print("\n❌ Transfer cancelled by user")
                break
        
        # Final stats
        elapsed = time.time() - self.start_time
        throughput = self.bytes_sent / elapsed if elapsed > 0 else 0
        
        print(f"\n✅ Transfer complete!")
        print(f"📊 Total time: {elapsed:.2f} seconds")
        print(f"📈 Average throughput: {throughput/1024:.1f} KB/s ({throughput*8/1000000:.2f} Mbps)")
        print(f"📦 Frames sent: {self.frames_sent}")
        
        cv2.destroyAllWindows()


class HVATPReceiver:
    """Complete receiver implementation"""
    
    def __init__(self,
                 visual_mode_colors: int = 4):
        """
        Initialize HVATP receiver
        
        Args:
            visual_mode_colors: Expected color mode (2, 4, or 8)
        """
        self.visual_decoder = VisualDecoder(
            expected_module_count=200,
            error_correction_level=0.35
        )
        
        self.visual_mode_colors = visual_mode_colors
        
        # Received data buffer
        self.received_frames = {}
        self.total_frames = None
        
        # Stats
        self.frames_decoded = 0
        self.frames_failed = 0
        self.start_time = None
        
    def receive_from_camera(self, 
                           camera_id: int = 0,
                           output_file: str = "received_file.bin",
                           display_window: str = "HVATP Receive"):
        """
        Receive file from camera
        
        Args:
            camera_id: Camera device ID
            output_file: Path to save received file
            display_window: OpenCV window name
        """
        print(f"📷 Opening camera {camera_id}...")
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print("❌ Failed to open camera")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ Camera ready")
        print("🎯 Point camera at transmitting device")
        print("Press 'q' to quit\n")
        
        cv2.namedWindow(display_window, cv2.WINDOW_NORMAL)
        self.start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break
            
            # Display camera view
            cv2.imshow(display_window, frame)
            
            # Try to decode
            result = self.visual_decoder.decode_frame(
                frame, color_mode=self.visual_mode_colors
            )
            
            if result and result.success:
                # Successfully decoded frame
                self.frames_decoded += 1
                
                # Store frame data
                self.received_frames[result.frame_id] = result.data
                
                if self.total_frames is None:
                    self.total_frames = result.total_frames
                    print(f"📊 Transfer started: {self.total_frames} frames expected")
                
                # Progress
                received_count = len(self.received_frames)
                progress = (received_count / self.total_frames * 100) if self.total_frames else 0
                
                elapsed = time.time() - self.start_time
                
                print(f"✅ Frame {result.frame_id}/{self.total_frames} | "
                      f"Progress: {progress:.1f}% | "
                      f"Success rate: {self.visual_decoder.get_success_rate()*100:.1f}% | "
                      f"Decode: {result.decode_time_ms:.1f}ms", end='\r')
                
                # Check if complete
                if received_count == self.total_frames:
                    print(f"\n🎉 All frames received!")
                    break
            
            # Check for quit
            key = cv2.waitKey(1)
            if key == ord('q'):
                print("\n❌ Receive cancelled by user")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Reconstruct file
        if self.received_frames:
            print("\n🔧 Reconstructing file...")
            self._reconstruct_file(output_file)
        else:
            print("\n❌ No frames received")
    
    def _reconstruct_file(self, output_file: str):
        """Reconstruct file from received frames"""
        # Sort frames by ID
        sorted_frames = [self.received_frames[i] for i in sorted(self.received_frames.keys())]
        
        # Concatenate data
        file_data = b''.join(sorted_frames)
        
        # Write to file
        with open(output_file, 'wb') as f:
            f.write(file_data)
        
        elapsed = time.time() - self.start_time
        throughput = len(file_data) / elapsed if elapsed > 0 else 0
        
        print(f"✅ File saved: {output_file}")
        print(f"📊 File size: {len(file_data)} bytes ({len(file_data)/1024:.1f} KB)")
        print(f"⏱️  Total time: {elapsed:.2f} seconds")
        print(f"📈 Average throughput: {throughput/1024:.1f} KB/s ({throughput*8/1000000:.2f} Mbps)")
        print(f"📦 Frames received: {len(self.received_frames)}/{self.total_frames}")
        print(f"✅ Success rate: {self.visual_decoder.get_success_rate()*100:.1f}%")


def demo_file_transfer():
    """
    Demo: Create test file and simulate transfer
    """
    print("="*60)
    print("   HVATP File Transfer Demo")
    print("="*60)
    print()
    
    # Create test file
    test_file = "test_data.bin"
    test_data = b"HVATP Test Data! " * 500  # ~8.5 KB
    
    with open(test_file, 'wb') as f:
        f.write(test_data)
    
    print(f"📝 Created test file: {test_file} ({len(test_data)} bytes)")
    print()
    
    # Sender mode
    print("🚀 Starting SENDER mode...")
    print("   (In real use, run on separate device)")
    print()
    
    sender = HVATPSender(
        visual_mode=EncodingMode.BALANCED,
        audio_modulation=ModulationType.QPSK
    )
    
    sender.send_file(test_file)
    
    print("\n" + "="*60)
    print("   Transfer Complete!")
    print("="*60)


def demo_receiver():
    """
    Demo: Receive mode (requires camera)
    """
    print("="*60)
    print("   HVATP Receiver Demo")
    print("="*60)
    print()
    
    receiver = HVATPReceiver(visual_mode_colors=4)
    receiver.receive_from_camera(
        camera_id=0,
        output_file="received_data.bin"
    )


def interactive_menu():
    """Interactive demo menu"""
    print("\n" + "="*60)
    print("   HVATP Interactive Demo")
    print("="*60)
    print()
    print("1. Send file (display on screen)")
    print("2. Receive file (from camera)")
    print("3. Full simulation (sender only)")
    print("4. Exit")
    print()
    
    choice = input("Select option (1-4): ").strip()
    
    if choice == '1':
        filepath = input("Enter file path to send: ").strip()
        if Path(filepath).exists():
            sender = HVATPSender()
            sender.send_file(filepath)
        else:
            print(f"❌ File not found: {filepath}")
    
    elif choice == '2':
        demo_receiver()
    
    elif choice == '3':
        demo_file_transfer()
    
    elif choice == '4':
        print("👋 Goodbye!")
        return
    
    else:
        print("❌ Invalid option")


if __name__ == "__main__":
    # Run interactive menu
    interactive_menu()
