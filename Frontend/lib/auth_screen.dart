import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'main.dart';

// Screen 1: Authentication Screen for Login and Sign Up
class AuthScreen extends StatefulWidget 
{
  @override
  _AuthScreenState createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> 
{
  bool isLogin = true;
  final usernameController = TextEditingController();
  final passwordController = TextEditingController();
  String message = "";

  Future<void> handleAuth() async 
  {
    // Determine URL based on login or signup
    final url      = Uri.parse("https://smartheart.onrender.com/${isLogin ? 'login' : 'signup'}");
    final response = await http.post
    (
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode
      ({
        "username": usernameController.text,
        "password": passwordController.text,
      }),
    ); // end handleAuth http post
       // submits http post request to Flask API

    try 
    {
      // Parse JSON response
      // decode the JSON response from the server in order to access its data
  final data = jsonDecode(response.body);

  if (response.statusCode == 200 || response.statusCode == 201) {
    setState(() => message = data["message"] ?? "Success");

    if (isLogin && data["user_id"] != null) 
    {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt("user_id", data["user_id"]);
      await prefs.setString("username", usernameController.text);

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => PredictionScreen()),
      );
    }
  } else 
  {
    setState(() => message = data["error"] ?? "Something went wrong");
  }
} catch (e) 
{
  setState(() => message = "Invalid response: ${response.body}");
}

    if (response.statusCode == 200 || response.statusCode == 201) {
      setState(() => message = data["message"] ?? "Success");

      // Save user_id to SharedPreferences if login
      if (isLogin && data["user_id"] != null) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt("user_id", data["user_id"]);
        await prefs.setString("username", usernameController.text);

        // Navigate to PredictionScreen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => PredictionScreen()),
        );
      }
    } else {
      setState(() => message = data["error"] ?? "Something went wrong");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32.0),
        child: Center(
          child: SingleChildScrollView(
            child: Column(
              children: [
                Icon(Icons.favorite, color: Colors.redAccent, size: 100),
                SizedBox(height: 30),
                TextField(
                  controller: usernameController,
                  decoration: InputDecoration(
                    hintText: 'Username',
                    filled: true,
                    fillColor: Colors.white12,
                    border: OutlineInputBorder(),
                  ),
                  style: TextStyle(color: Colors.white),
                ),
                SizedBox(height: 16),
                TextField(
                  controller: passwordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    hintText: 'Password',
                    filled: true,
                    fillColor: Colors.white12,
                    border: OutlineInputBorder(),
                  ),
                  style: TextStyle(color: Colors.white),
                ),
                SizedBox(height: 20),
                ElevatedButton(
                  onPressed: handleAuth,
                  child: Text(isLogin ? "Login" : "Sign Up"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.redAccent,
                    padding: EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                  ),
                ),
                TextButton(
                  onPressed: () => setState(() => isLogin = !isLogin),
                  child: Text(
                    isLogin ? "Don't have an account? Sign Up" : "Already have an account? Log In",
                    style: TextStyle(color: Colors.white70),
                  ),
                ),
                if (message.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 16),
                    child: Text(
                      message,
                      style: TextStyle(color: Colors.redAccent),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}