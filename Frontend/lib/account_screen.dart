import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';


// ========== Account Screen ==========
// Displays current user's username and allows logout
class AccountScreen extends StatefulWidget {
  @override
  _AccountScreenState createState() => _AccountScreenState();
}


class _AccountScreenState extends State<AccountScreen> {
  String? username;  // Stores the currently logged-in username

  @override
  void initState() {
    super.initState();
    loadUserData();  // Load stored username when screen initializes
  }


  // Loads the username from SharedPreferences
  Future<void> loadUserData() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      username = prefs.getString('username');
    });
  }


  // Clears stored user data and redirects to login screen
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();  // Clears user_id and username
    Navigator.of(context).pushReplacementNamed('/login');
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,  // Dark theme background
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 60.0),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Profile icon
              Icon(Icons.account_circle, size: 100, color: Colors.redAccent),
              SizedBox(height: 20),

              // Display username (fallback: "username")
              Text(
                "Username:\n${username ?? 'username'}",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),

              SizedBox(height: 30),

              // Log Out Button
              ElevatedButton(
                onPressed: logout,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  padding: EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                ),
                child: Text("Log Out", style: TextStyle(fontSize: 16)),
              ),

              // Extra space at the bottom
              SizedBox(height: 400),
            ],
          ),
        ),
      ),
    );
  }
}