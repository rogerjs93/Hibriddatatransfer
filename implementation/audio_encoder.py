"""
HVATP Audio Encoder
Implements OFDM-based audio data transmission
"""

import numpy as np
from typing import List, Tuple
from enum import Enum
import struct


class ModulationType(Enum):
    """Audio modulation schemes"""
    BPSK = 1   # 1 bit/symbol - most robust
    QPSK = 2   # 2 bits/symbol - balanced
    QAM16 = 4  # 4 bits/symbol - high throughput


class AudioEncoder:
    """
    OFDM-based audio encoder for metadata and control channel
    """
    
    def __init__(self,
                 sample_rate: int = 48000,
                 num_subcarriers: int = 48,
                 carrier_start: float = 2500.0,
                 carrier_spacing: float = 250.0,
                 modulation: ModulationType = ModulationType.QPSK,
                 packet_duration: float = 0.05):  # 50ms packets
        """
        Args:
            sample_rate: Audio sampling rate (Hz)
            num_subcarriers: Number of OFDM subcarriers
            carrier_start: Starting frequency (Hz)
            carrier_spacing: Spacing between carriers (Hz)
            modulation: Modulation scheme
            packet_duration: Duration of each audio packet (seconds)
        """
        self.sample_rate = sample_rate
        self.num_subcarriers = num_subcarriers
        self.carrier_start = carrier_start
        self.carrier_spacing = carrier_spacing
        self.modulation = modulation
        self.packet_duration = packet_duration
        
        # Calculate derived parameters
        self.samples_per_packet = int(sample_rate * packet_duration)
        self.symbol_duration = packet_duration / 4  # 4 symbols per packet
        self.samples_per_symbol = int(sample_rate * self.symbol_duration)
        
        # Generate carrier frequencies
        self.carrier_freqs = np.array([
            carrier_start + i * carrier_spacing
            for i in range(num_subcarriers)
        ])
        
        # Precompute carrier waves
        t = np.arange(self.samples_per_symbol) / sample_rate
        self.carrier_waves = np.array([
            np.exp(2j * np.pi * freq * t)
            for freq in self.carrier_freqs
        ])
        
    def _generate_preamble(self) -> np.ndarray:
        """Generate chirp preamble for timing synchronization"""
        duration = 0.005  # 5ms chirp
        samples = int(self.sample_rate * duration)
        
        t = np.arange(samples) / self.sample_rate
        
        # Linear chirp from carrier_start to carrier_start + bandwidth
        f0 = self.carrier_start
        f1 = self.carrier_freqs[-1]
        
        chirp = np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t**2 / (2 * duration)))
        
        # Apply window to reduce sidelobes
        window = np.hanning(samples)
        chirp = chirp * window * 0.8  # 80% amplitude
        
        return chirp
        
    def _generate_sync_word(self) -> np.ndarray:
        """Generate known sync sequence for frame detection"""
        duration = 0.002  # 2ms
        samples = int(self.sample_rate * duration)
        
        # Barker-like sequence on pilot tones
        pilot_freqs = self.carrier_freqs[::4]  # Every 4th carrier
        sequence = [1, 1, 1, -1, -1, 1, -1]  # Barker-7
        
        t = np.arange(samples) / self.sample_rate
        sync = np.zeros(samples)
        
        for i, freq in enumerate(pilot_freqs[:len(sequence)]):
            phase = sequence[i % len(sequence)]
            sync += np.sin(2 * np.pi * freq * t + (0 if phase > 0 else np.pi))
            
        sync = sync / len(pilot_freqs)
        sync = sync * 0.6  # 60% amplitude
        
        return sync
        
    def _encode_header(self, 
                       frame_id: int,
                       packet_seq: int,
                       payload_type: int) -> bytes:
        """
        Encode packet header
        
        Returns:
            8 bytes of header data
        """
        header = bytearray(8)
        header[0:3] = frame_id.to_bytes(3, 'big')
        header[3:5] = packet_seq.to_bytes(2, 'big')
        header[5] = payload_type & 0xFF
        
        # CRC-16
        crc = self._calculate_crc16(header[:6])
        header[6:8] = crc.to_bytes(2, 'big')
        
        return bytes(header)
        
    def _calculate_crc16(self, data: bytes) -> int:
        """Simple CRC-16 implementation"""
        crc = 0xFFFF
        poly = 0x1021
        
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ poly
                else:
                    crc = crc << 1
                crc &= 0xFFFF
                
        return crc
        
    def _modulate_symbols(self, bits: bytes) -> np.ndarray:
        """
        Modulate bits onto subcarriers
        
        Returns:
            Complex symbol values for each subcarrier
        """
        symbols = np.zeros(self.num_subcarriers, dtype=complex)
        
        bit_string = ''.join(format(b, '08b') for b in bits)
        bits_per_symbol = self.modulation.value
        
        for i in range(self.num_subcarriers):
            start_bit = i * bits_per_symbol
            end_bit = start_bit + bits_per_symbol
            
            if end_bit <= len(bit_string):
                symbol_bits = bit_string[start_bit:end_bit]
                symbols[i] = self._bits_to_symbol(symbol_bits)
                
        return symbols
        
    def _bits_to_symbol(self, bits: str) -> complex:
        """Convert bit string to complex symbol (constellation point)"""
        value = int(bits, 2)
        
        if self.modulation == ModulationType.BPSK:
            # BPSK: 0 → +1, 1 → -1
            return 1.0 if value == 0 else -1.0
            
        elif self.modulation == ModulationType.QPSK:
            # QPSK: 4 constellation points
            constellation = [
                1 + 1j,   # 00
                1 - 1j,   # 01
                -1 + 1j,  # 10
                -1 - 1j   # 11
            ]
            return constellation[value] / np.sqrt(2)
            
        elif self.modulation == ModulationType.QAM16:
            # 16-QAM: 16 constellation points
            # Map to 4x4 grid: -3, -1, +1, +3
            I = ((value >> 2) & 0x3) * 2 - 3  # In-phase
            Q = (value & 0x3) * 2 - 3          # Quadrature
            return (I + 1j * Q) / np.sqrt(10)
            
    def _ofdm_modulate(self, symbols: np.ndarray) -> np.ndarray:
        """
        Modulate symbols onto carriers using OFDM
        
        Returns:
            Real-valued audio samples
        """
        audio = np.zeros(self.samples_per_symbol, dtype=float)
        
        for i, symbol in enumerate(symbols):
            # Multiply symbol by carrier wave
            modulated = symbol * self.carrier_waves[i]
            audio += modulated.real  # Take real part
            
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.7
        
        return audio
        
    def _add_cyclic_prefix(self, ofdm_symbol: np.ndarray, prefix_ratio: float = 0.1) -> np.ndarray:
        """Add cyclic prefix to combat multipath interference"""
        prefix_len = int(len(ofdm_symbol) * prefix_ratio)
        prefix = ofdm_symbol[-prefix_len:]
        return np.concatenate([prefix, ofdm_symbol])
        
    def encode_packet(self,
                      payload: bytes,
                      frame_id: int = 0,
                      packet_seq: int = 0,
                      payload_type: int = 0x01) -> np.ndarray:
        """
        Encode a complete audio packet
        
        Args:
            payload: Data to transmit (max ~150 bytes depending on modulation)
            frame_id: Reference to visual frame ID
            packet_seq: Packet sequence number
            payload_type: Type of payload (see protocol spec)
            
        Returns:
            Audio samples as float array (-1.0 to +1.0)
        """
        # 1. Generate preamble (5ms)
        preamble = self._generate_preamble()
        
        # 2. Generate sync word (2ms)
        sync = self._generate_sync_word()
        
        # 3. Encode header (8ms - 2 OFDM symbols)
        header = self._encode_header(frame_id, packet_seq, payload_type)
        header_symbols1 = self._modulate_symbols(header[:4])
        header_symbols2 = self._modulate_symbols(header[4:8])
        
        header_audio1 = self._ofdm_modulate(header_symbols1)
        header_audio2 = self._ofdm_modulate(header_symbols2)
        
        # 4. Encode payload (multiple OFDM symbols to fill 30ms)
        payload_audio = []
        bits_per_symbol_set = (self.num_subcarriers * self.modulation.value) // 8
        
        for i in range(0, len(payload), bits_per_symbol_set):
            chunk = payload[i:i + bits_per_symbol_set]
            # Pad if necessary
            if len(chunk) < bits_per_symbol_set:
                chunk = chunk + b'\x00' * (bits_per_symbol_set - len(chunk))
                
            symbols = self._modulate_symbols(chunk)
            audio = self._ofdm_modulate(symbols)
            payload_audio.append(audio)
            
        payload_audio = np.concatenate(payload_audio) if payload_audio else np.array([])
        
        # 5. Combine all parts
        packet = np.concatenate([
            preamble,
            sync,
            header_audio1,
            header_audio2,
            payload_audio
        ])
        
        # 6. Pad or truncate to exact packet duration
        target_samples = self.samples_per_packet
        if len(packet) < target_samples:
            packet = np.concatenate([packet, np.zeros(target_samples - len(packet))])
        elif len(packet) > target_samples:
            packet = packet[:target_samples]
            
        return packet.astype(np.float32)
        
        
class PacketType:
    """Payload type identifiers"""
    FRAME_SYNC = 0x01
    OPERATORS = 0x02
    PRNG_SEEDS = 0x03
    VISUAL_PARITY = 0x04
    DICTIONARY = 0x05
    CONTROL = 0x06
    

class AudioPacketBuilder:
    """Helper class to build different types of audio packets"""
    
    def __init__(self, encoder: AudioEncoder):
        self.encoder = encoder
        
    def build_ack_packet(self, 
                         frame_id: int,
                         ack_bitmap: int,
                         packet_seq: int = 0) -> np.ndarray:
        """
        Build ACK/NACK packet
        
        Args:
            frame_id: Current visual frame ID
            ack_bitmap: Bitmap of successfully received frames
            packet_seq: Packet sequence number
        """
        payload = struct.pack('>Q', ack_bitmap)  # 8 bytes = 64 frames
        return self.encoder.encode_packet(
            payload, frame_id, packet_seq, PacketType.FRAME_SYNC
        )
        
    def build_operator_packet(self,
                             frame_id: int,
                             operators: List[Tuple[int, bytes]],
                             packet_seq: int = 0) -> np.ndarray:
        """
        Build operator instruction packet
        
        Args:
            operators: List of (opcode, parameters) tuples
        """
        payload = bytearray()
        for opcode, params in operators:
            payload.append(opcode)
            payload.extend(params)
            
        return self.encoder.encode_packet(
            bytes(payload), frame_id, packet_seq, PacketType.OPERATORS
        )
        
    def build_prng_packet(self,
                         frame_id: int,
                         algorithm: int,
                         seed: int,
                         length: int,
                         packet_seq: int = 0) -> np.ndarray:
        """Build PRNG seed packet"""
        payload = struct.pack('>BIQ', algorithm, seed, length)
        return self.encoder.encode_packet(
            payload, frame_id, packet_seq, PacketType.PRNG_SEEDS
        )
        

# Example usage
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from scipy.io import wavfile
    
    # Create encoder
    encoder = AudioEncoder(
        sample_rate=48000,
        num_subcarriers=48,
        modulation=ModulationType.QPSK
    )
    
    # Create packet builder
    builder = AudioPacketBuilder(encoder)
    
    # Build test ACK packet
    packet = builder.build_ack_packet(
        frame_id=42,
        ack_bitmap=0xFFFFFFFFFFFFFFFF  # All frames ACKed
    )
    
    print(f"Generated audio packet: {len(packet)} samples ({len(packet)/48000:.3f} seconds)")
    
    # Save as WAV for testing
    wavfile.write("test_packet.wav", 48000, (packet * 32767).astype(np.int16))
    print("Saved test packet to test_packet.wav")
    
    # Plot spectrum
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(packet[:1000])
    plt.title("Time Domain (first 1000 samples)")
    plt.xlabel("Sample")
    plt.ylabel("Amplitude")
    
    plt.subplot(1, 2, 2)
    freqs = np.fft.rfftfreq(len(packet), 1/48000)
    spectrum = np.abs(np.fft.rfft(packet))
    plt.plot(freqs, 20 * np.log10(spectrum + 1e-10))
    plt.title("Frequency Spectrum")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    plt.xlim(0, 20000)
    
    plt.tight_layout()
    plt.savefig("audio_packet_analysis.png")
    print("Saved spectrum analysis to audio_packet_analysis.png")
