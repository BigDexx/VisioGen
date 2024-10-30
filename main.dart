import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:gallery_saver/gallery_saver.dart';
import 'package:permission_handler/permission_handler.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Video Generator',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: HighlightTextInputPage(),
    );
  }
}

class HighlightTextInputPage extends StatefulWidget {
  @override
  _HighlightTextInputPageState createState() => _HighlightTextInputPageState();
}

class _HighlightTextInputPageState extends State<HighlightTextInputPage> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  String _selectedFont = 'naname-goma';
  String _selectedVideoType = 'Minecraft';
  String _selectedVoiceType = 'Male';

  bool _isLoading = false;
  String? _videoUrl;

  @override
  void initState() {
    super.initState();
    requestStoragePermission();
  }

  Future<void> requestStoragePermission() async {
    if (await Permission.storage.request().isGranted) {
      // Storage permission granted
    } else if (await Permission.storage.isPermanentlyDenied) {
      openAppSettings(); // Prompt user to settings if permission is permanently denied
    }
  }

  Future<void> sendDataToBackend() async {
    setState(() {
      _isLoading = true;
      _videoUrl = null;
    });

    final Uri url = Uri.parse('http://15.206.80.220:5000/endpoint');
    try {
      final response = await http.post(
        url,
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: jsonEncode(<String, dynamic>{
          'text': _controller.text,
          'font': _selectedFont,
          'videoType': _selectedVideoType,
          'voiceType': _selectedVoiceType,
        }),
      ).timeout(Duration(seconds: 300));

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        setState(() {
          _videoUrl = responseData['video_url'];
          _isLoading = false;
        });
      } else {
        setState(() => _isLoading = false);
        _showSnackBar('Failed to send data: ${response.statusCode}');
      }
    } catch (e) {
      setState(() => _isLoading = false);
      _showSnackBar('An error occurred: $e');
    }
  }

  Future<void> downloadVideo() async {
    if (_videoUrl == null) return;

    // Request permissions if needed before downloading the video
    if (await Permission.storage.request().isGranted) {
      final response = await http.get(Uri.parse(_videoUrl!));
      if (response.statusCode == 200) {
        final Directory appDir = await getApplicationDocumentsDirectory();
        final String fileName = 'random_subclip_with_audio(captioned).mp4';
        final String filePath = '${appDir.path}/$fileName';

        final File videoFile = File(filePath);
        await videoFile.writeAsBytes(response.bodyBytes);

        final bool success = await GallerySaver.saveVideo(filePath) ?? false;

        if (success) {
          _showSnackBar('Video saved to gallery: $fileName');
        } else {
          _showSnackBar('Failed to save video to gallery!');
        }
      } else {
        _showSnackBar('Failed to download video: ${response.statusCode}');
      }
    } else if (await Permission.storage.isPermanentlyDenied) {
      openAppSettings(); // Prompt user to settings if permission is permanently denied
    } else {
      _showSnackBar('Required permissions denied! Please enable them in the settings.');
    }
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Highlight Text Input'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildLabel('Enter your story:'),
            _buildTextInput(),
            SizedBox(height: 16),
            _buildDropdown(
              label: 'Choose a Font:',
              currentValue: _selectedFont,
              options: ['naname-goma', 'Handscript', 'Shikaku-serif', 'Arvo-Bold'],
              onChanged: (newValue) => setState(() => _selectedFont = newValue!),
            ),
            SizedBox(height: 16),
            _buildDropdown(
              label: 'Choose Video Type:',
              currentValue: _selectedVideoType,
              options: ['Minecraft', 'GTA', 'Dragon Ball', 'COD'],
              onChanged: (newValue) => setState(() => _selectedVideoType = newValue!),
            ),
            SizedBox(height: 16),
            _buildDropdown(
              label: 'Choose Voice Type:',
              currentValue: _selectedVoiceType,
              options: ['Male', 'Female'],
              onChanged: (newValue) => setState(() => _selectedVoiceType = newValue!),
            ),
            SizedBox(height: 16),
            _isLoading
                ? Center(child: CircularProgressIndicator())
                : ElevatedButton(
              onPressed: sendDataToBackend,
              child: Text('Continue to Video'),
            ),
            if (_videoUrl != null)
              ElevatedButton(
                onPressed: downloadVideo,
                child: Text('Download Video'),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildTextInput() {
    return Container(
      height: 200,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.blueAccent, width: 2),
        borderRadius: BorderRadius.circular(8),
      ),
      child: SingleChildScrollView(
        controller: _scrollController,
        child: TextField(
          controller: _controller,
          maxLines: null,
          decoration: InputDecoration(
            hintText: 'Type your story here...',
            border: InputBorder.none,
            contentPadding: EdgeInsets.all(16),
          ),
        ),
      ),
    );
  }

  Widget _buildDropdown({
    required String label,
    required String currentValue,
    required List<String> options,
    required ValueChanged<String?> onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildLabel(label),
        DropdownButton<String>(
          value: currentValue,
          onChanged: onChanged,
          items: options.map<DropdownMenuItem<String>>((String value) {
            return DropdownMenuItem<String>(
              value: value,
              child: Text(value),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildLabel(String label) {
    return Text(
      label,
      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
    );
  }
}
