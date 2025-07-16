// --- graph_screen.dart ---
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';

class GraphScreen extends StatefulWidget {
  @override
  _GraphScreenState createState() => _GraphScreenState();
}

class _GraphScreenState extends State<GraphScreen> {
  List<FlSpot> bpmPoints = [];
  List<FlSpot> spo2Points = [];
  bool isLoading = true;
  String errorMessage = '';

  @override
  void initState() {
    super.initState();
    fetchGraphData();
  }

  Future<void> fetchGraphData() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getInt('user_id');
    if (userId == null) {
      setState(() {
        errorMessage = 'No user ID found.';
        isLoading = false;
      });
      return;
    }

    final url = Uri.parse('https://smartheart-backend.onrender.com/get-readings?user_id=$userId');
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        List<FlSpot> bpm = [];
        List<FlSpot> spo2 = [];

        for (int i = 0; i < data.length; i++) {
          bpm.add(FlSpot(i.toDouble(), data[i]['bpm'].toDouble()));
          spo2.add(FlSpot(i.toDouble(), data[i]['spo2'].toDouble()));
        }

        setState(() {
          bpmPoints = bpm;
          spo2Points = spo2;
          isLoading = false;
        });
      } else {
        setState(() {
          errorMessage = 'Failed to load data';
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        errorMessage = 'Error: $e';
        isLoading = false;
      });
    }
  }

  LineChartData lineChartData(List<FlSpot> points, String label, Color color) {
    return LineChartData(
      lineBarsData: [
        LineChartBarData(
          spots: points,
          isCurved: true,
          colors: [color],
          barWidth: 2,
          belowBarData: BarAreaData(show: false),
          dotData: FlDotData(show: false),
        ),
      ],
      titlesData: FlTitlesData(
        bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        leftTitles: AxisTitles(
          sideTitles: SideTitles(showTitles: true, reservedSize: 30),
        ),
      ),
      gridData: FlGridData(show: true),
      borderData: FlBorderData(show: true),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Vitals Graph'),
        backgroundColor: Colors.redAccent.shade700,
      ),
      backgroundColor: Colors.black,
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : errorMessage.isNotEmpty
              ? Center(child: Text(errorMessage, style: TextStyle(color: Colors.redAccent)))
              : SingleChildScrollView(
                  padding: EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      Text('BPM Over Time', style: TextStyle(color: Colors.white, fontSize: 20)),
                      SizedBox(
                        height: 200,
                        child: LineChart(lineChartData(bpmPoints, 'BPM', Colors.redAccent)),
                      ),
                      SizedBox(height: 40),
                      Text('SpO₂ Over Time', style: TextStyle(color: Colors.white, fontSize: 20)),
                      SizedBox(
                        height: 200,
                        child: LineChart(lineChartData(spo2Points, 'SpO₂', Colors.lightBlueAccent)),
                      ),
                    ],
                  ),
                ),
    );
  }
}