import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';
import 'auth_screen.dart';
import 'prediction_screen.dart';

class AccountScreen extends StatefulWidget {
  @override
  _AccountScreenState createState() => _AccountScreenState();
}

class _AccountScreenState extends State<AccountScreen> {
  String? username;
  List<dynamic> readings = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    loadUserData();
    fetchReadings();
  }

  Future<void> loadUserData() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      username = prefs.getString('username');
    });
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (context) => AuthScreen()),
      (route) => false,
    );
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
        setState(() => isLoading = false);
      }
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  List<FlSpot> buildBpmSpots() {
    return List.generate(readings.length, (index) {
      return FlSpot(index.toDouble(), (readings[index]['bpm'] as num).toDouble());
    });
  }

  List<FlSpot> buildSpo2Spots() {
    return List.generate(readings.length, (index) {
      return FlSpot(index.toDouble(), (readings[index]['spo2'] as num).toDouble());
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 60.0),
        child: isLoading
            ? Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Icon(Icons.account_circle, size: 100, color: Colors.redAccent),
                    SizedBox(height: 20),
                    Text(
                      "Username:\n${username ?? 'username'}",
                      style: TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    SizedBox(height: 30),

                    Text("Health History", style: TextStyle(fontSize: 22, color: Colors.white)),
                    Divider(color: Colors.white),
                    ListView.builder(
                      shrinkWrap: true,
                      physics: NeverScrollableScrollPhysics(),
                      itemCount: readings.length,
                      itemBuilder: (context, index) {
                        final r = readings[index];
                        return ListTile(
                          title: Text("BPM: ${r['bpm']}  |  SpO₂: ${r['spo2']}%",
                              style: TextStyle(color: Colors.white)),
                          subtitle: Text("${r['timestamp']}", style: TextStyle(color: Colors.grey)),
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

                    SizedBox(height: 20),
                    Text("Vitals Over Time", style: TextStyle(fontSize: 22, color: Colors.white)),
                    Divider(color: Colors.white),
                    SizedBox(
                      height: 200,
                      child: LineChart(
                        LineChartData(
                          titlesData: FlTitlesData(show: false),
                          borderData: FlBorderData(show: false),
                          lineBarsData: [
                            LineChartBarData(
                              spots: buildBpmSpots(),
                              isCurved: true,
                              color: Colors.redAccent,
                              belowBarData: BarAreaData(show: false),
                            ),
                            LineChartBarData(
                              spots: buildSpo2Spots(),
                              isCurved: true,
                              color: Colors.lightBlueAccent,
                              belowBarData: BarAreaData(show: false),
                            ),
                          ],
                        ),
                      ),
                    ),

                    SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: () {
                        Navigator.pushNamed(context, '/prediction');
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blueGrey,
                        padding: EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                      ),
                      child: Text("Back to Monitor", style: TextStyle(fontSize: 16)),
                    ),
                    SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: logout,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        padding: EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                      ),
                      child: Text("Log Out", style: TextStyle(fontSize: 16)),
                    ),
                    SizedBox(height: 40),
                  ],
                ),
              ),
      ),
    );
  }
}