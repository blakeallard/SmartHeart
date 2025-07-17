// --- health_history_screen.dart ---
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class HealthHistoryScreen extends StatefulWidget {
  @override
  _HealthHistoryScreenState createState() => _HealthHistoryScreenState();
}

class _HealthHistoryScreenState extends State<HealthHistoryScreen> {
  List<dynamic> readings = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchReadings();
  }

  Future<void> fetchReadings() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getInt('user_id');
    final url = Uri.parse("https://smartheart-backend.onrender.com/get-readings?user_id=$userId");

    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          readings = data;
          isLoading = false;
        });
      } else {
        setState(() {
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Health History"),
        backgroundColor: Colors.redAccent.shade700,
      ),
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : readings.isEmpty
              ? Center(child: Text("No history found."))
              : ListView.builder(
                  itemCount: readings.length,
                  itemBuilder: (context, index) {
                    final r = readings[index];
                    return ListTile(
                      title: Text("BPM: ${r['bpm']}  |  SpO₂: ${r['spo2']}%"),
                      subtitle: Text("${r['timestamp']}", style: TextStyle(fontSize: 12)),
                      trailing: Text(
                        r['prediction'] == 1 ? 'Healthy' : 'Not Healthy',
                        style: TextStyle(
                          color: r['prediction'] == 1 ? Colors.greenAccent : Colors.redAccent,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}