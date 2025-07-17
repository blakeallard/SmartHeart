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
  String message = "";  // Used to show error/success messages


  // Handle login/signup button press
  Future<void> handleAuth() async {
    // Determine which endpoint to use based on mode
    final url = Uri.parse(
      "https://smartheart.onrender.com/${isLogin ? 'login' : 'signup'}",
    );


    // Send HTTP POST request to Flask API
    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "username": usernameController.text,
        "password": passwordController.text,
      }),
    );


    try {
      // Decode the JSON response from the server
      final data = jsonDecode(response.body);


      // If successful login/signup
      if (response.statusCode == 200 || response.statusCode == 201) {
        setState(() => message = data["message"] ?? "Success");


        // If it's a login and we got a user_id, store credentials locally
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
        // Handle failure with server-provided error message
        setState(() => message = data["error"] ?? "Something went wrong");
      }
    } catch (e) {
      // If decoding JSON fails
      setState(() => message = "Invalid response: ${response.body}");
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
