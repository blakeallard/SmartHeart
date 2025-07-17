import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'main.dart';  // Import main.dart to access PredictionScreen


// ====== Screen: Authentication (Login & Sign Up) ======
class AuthScreen extends StatefulWidget {
  @override
  _AuthScreenState createState() => _AuthScreenState();
}


class _AuthScreenState extends State<AuthScreen> {
  bool isLogin = true;  // Tracks if we’re in login or signup mode
  final usernameController = TextEditingController();
  final passwordController = TextEditingController();
  String message = "";

Future<void> handleAuth() async {
  final url = Uri.parse("https://smartheart-backend.onrender.com/${isLogin ? 'login' : 'signup'}");

  try {
    // ✅ Submit the request to Flask API
    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "username": usernameController.text,
        "password": passwordController.text,
      }),
    );

    // Decode JSON response only once
    final data = jsonDecode(response.body);

    if (response.statusCode == 200 || response.statusCode == 201) {
      setState(() => message = data["message"] ?? "Success");

      // Save user_id if login was successful
      if (isLogin && data["user_id"] != null) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt("user_id", data["user_id"]);
        await prefs.setString("username", usernameController.text);

        // Navigate to Prediction screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => PredictionScreen()),
        );
      }

    } else {
      // Error returned from backend
      setState(() => message = data["error"] ?? "Something went wrong");
    }

  } catch (e) {
    // Failed to decode or network error
    setState(() => message = "Invalid response: $e");
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
                // App Icon
                Icon(Icons.favorite, color: Colors.redAccent, size: 100),
                SizedBox(height: 30),

                // Username TextField
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

                // Password TextField
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

                // Login/Signup button
                ElevatedButton(
                  onPressed: handleAuth,
                  child: Text(isLogin ? "Login" : "Sign Up"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.redAccent,
                    padding: EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                  ),
                ),

                // Toggle between login and signup
                TextButton(
                  onPressed: () => setState(() => isLogin = !isLogin),
                  child: Text(
                    isLogin
                        ? "Don't have an account? Sign Up"
                        : "Already have an account? Log In",
                    style: TextStyle(color: Colors.white70),
                  ),
                ),

                // Display success or error message
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
