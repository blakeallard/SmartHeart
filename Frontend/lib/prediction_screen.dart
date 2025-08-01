import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:socket_io_client/socket_io_client.dart' as IO;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'auth_screen.dart';
import 'account_screen.dart';

class PredictionScreen extends StatefulWidget {
  @override
  _PredictionScreenState createState() => _PredictionScreenState();
}

class _PredictionScreenState extends State<PredictionScreen>
    with SingleTickerProviderStateMixin {
  String result = 'No prediction yet';
  int bpm = 72;
  int spo2 = 98;
  late AnimationController _controller;
  late Animation<double> _pulseAnimation;
  late IO.Socket socket;
  List<int> waveformPoints = [];

  @override
  void initState() {
    super.initState();
    fetchLatestDataFromDB();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.9, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    socket = IO.io('https://smartheart-backend.onrender.com', {
      'transports': ['websocket'],
      'autoConnect': true,
    });

    socket.on('waveform', (data) {
      if (data["bpm"] != null && data["spo2"] != null) {
        setState(() {
          bpm = data["bpm"];
          spo2 = data["spo2"];
          waveformPoints.add(bpm);
          if (waveformPoints.length > 50) {
            waveformPoints.removeAt(0);
          }

          double scaleMin = 0.9;
          double scaleMax = bpm > 100 ? 1.3 : 1.1;
          _pulseAnimation = Tween<double>(begin: scaleMin, end: scaleMax).animate(
            CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
          );
          _controller.duration = Duration(milliseconds: (60000 ~/ bpm).clamp(600, 2000));
          if (!_controller.isAnimating) _controller.repeat(reverse: true);
        });
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    socket.disconnect();
    super.dispose();
  }

  Future<void> fetchLatestDataFromDB() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getInt('user_id');

    if (userId == null) {
      setState(() {
        result = "No user ID found in SharedPreferences.";
      });
      return;
    }

    final url = Uri.parse("https://smartheart-backend.onrender.com/latest-data?user_id=$userId");

    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          bpm = data['bpm'];
          spo2 = data['spo2'];
          result = "Last recorded: BPM ${data['bpm']}, SpO₂ ${data['spo2']}%";
        });
      } else {
        setState(() {
          result = "Failed to fetch: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        result = "Error: $e";
      });
    }
  }

  bool _isSubmitting = false;
  int? _lastSubmittedBpm;
  int? _lastSubmittedSpo2;

  Future<void> sendPredictionRequest(int bpm, int spo2) async {
    if (_isSubmitting) return;
    if (bpm == _lastSubmittedBpm && spo2 == _lastSubmittedSpo2) {
      print("Duplicate reading. Skipping submission.");
      setState(() {
        result = "Same reading already submitted. Check account history.";
      });
      return;
    }

    setState(() => _isSubmitting = true);

    final predictUrl = Uri.parse('https://smartheart-backend.onrender.com/predict');
    final readingUrl = Uri.parse('https://smartheart-backend.onrender.com/submit-reading');

    try {
      final response = await http.post(
        predictUrl,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"bpm": bpm, "spo2": spo2}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final prediction = data['prediction'];

        setState(() {
          if (prediction == 1) {
            result = "Prediction: Healthy";
          } else if (prediction == 0) {
            result = "Prediction: Not Healthy";
          } else {
            result = "Prediction: Unknown";
          }

          _lastSubmittedBpm = bpm;
          _lastSubmittedSpo2 = spo2;
        });

        final prefs = await SharedPreferences.getInstance();
        final userId = prefs.getInt('user_id');

        if (userId != null) {
          await http.post(
            readingUrl,
            headers: {"Content-Type": "application/json"},
            body: jsonEncode({
              "user_id": userId,
              "bpm": bpm,
              "spo2": spo2,
              "timestamp": DateTime.now().toIso8601String(),
            }),
          );
        } else {
          print("No user_id found in SharedPreferences");
        }
      } else {
        setState(() {
          result = "Server Error: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        result = "Error: $e";
      });
    } finally {
      setState(() => _isSubmitting = false);
      Navigator.pushNamed(context, '/account');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Health Monitor'),
        backgroundColor: Colors.redAccent.shade700,
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.account_circle),
            onPressed: () {
              Navigator.pushNamed(context, '/account');
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          Positioned.fill(
            child: Image.asset('assets/backgrounds/home_background.jpg', fit: BoxFit.cover),
          ),
          Positioned.fill(
            child: Container(color: Colors.black.withOpacity(0.3)),
          ),
          Center(
            child: ScaleTransition(
              scale: _pulseAnimation,
              child: Container(
                width: 300,
                height: 300,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [Colors.redAccent.withOpacity(0.4), Colors.transparent],
                    stops: [0.3, 1.0],
                  ),
                ),
              ),
            ),
          ),
          Center(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ScaleTransition(
                    scale: _pulseAnimation,
                    child: ShaderMask(
                      shaderCallback: (bounds) {
                        return RadialGradient(
                          center: Alignment.topLeft,
                          radius: 1.0,
                          colors: [
                            Colors.redAccent.shade200,
                            Colors.redAccent.shade700,
                            Colors.black,
                          ],
                          stops: [0.1, 0.6, 1.0],
                        ).createShader(bounds);
                      },
                      blendMode: BlendMode.srcIn,
                      child: const Icon(Icons.favorite, size: 120),
                    ),
                  ),
                  const SizedBox(height: 30),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.monitor_heart, color: Colors.redAccent, size: 30),
                      const SizedBox(width: 8),
                      Text('BPM: $bpm', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w600)),
                    ],
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.bubble_chart, color: Colors.lightBlueAccent, size: 30),
                      const SizedBox(width: 8),
                      Text('SpO₂: $spo2%', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w600)),
                    ],
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    height: 100,
                    width: double.infinity,
                    child: CustomPaint(painter: WaveformPainter(waveformPoints)),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _isSubmitting ? Colors.grey : Colors.redAccent,
                      padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 16),
                    ),
                    onPressed: _isSubmitting ? null : () => sendPredictionRequest(bpm, spo2),
                    child: _isSubmitting
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Submit Data', style: TextStyle(fontSize: 18)),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    result,
                    style: TextStyle(
                      fontSize: 18,
                      color: result.contains("Healthy")
                          ? Colors.greenAccent
                          : (result.contains("Not Healthy") ? Colors.redAccent : Colors.white70),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class WaveformPainter extends CustomPainter {
  final List<int> points;
  WaveformPainter(this.points);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.redAccent
      ..strokeWidth = 2;

    for (int i = 0; i < points.length - 1; i++) {
      final x1 = i * (size.width / points.length);
      final y1 = size.height - (points[i].toDouble() * size.height / 150);
      final x2 = (i + 1) * (size.width / points.length);
      final y2 = size.height - (points[i + 1].toDouble() * size.height / 150);
      canvas.drawLine(Offset(x1, y1), Offset(x2, y2), paint);
    }
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => true;
}