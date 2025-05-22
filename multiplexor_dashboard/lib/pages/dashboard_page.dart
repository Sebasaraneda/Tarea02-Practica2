import 'package:flutter/material.dart';
import 'dart:async';
import 'vista_general_tab.dart';
import 'multiplexor_tab.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  late String _dateTime;
  late Timer _timer;

  @override
  void initState() {
    super.initState();
    _dateTime = _getCurrentDateTime();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() {
        _dateTime = _getCurrentDateTime();
      });
    });
  }

  String _getCurrentDateTime() {
    final now = DateTime.now();
    return "${now.year}-${_twoDigits(now.month)}-${_twoDigits(now.day)} "
           "${_twoDigits(now.hour)}:${_twoDigits(now.minute)}:${_twoDigits(now.second)}";
  }

  String _twoDigits(int n) => n.toString().padLeft(2, '0');

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Row(
            children: [
              const Expanded(
                child: Text('Monitoreo Sensores', textAlign: TextAlign.center),
              ),
              Text(
                _dateTime,
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w400),
              ),
            ],
          ),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Vista General'),
              Tab(text: 'Multiplexor 1'),
              Tab(text: 'Multiplexor 2'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            VistaGeneralTab(),
            MultiplexorTable(multiplexorKey: 'Multiplexor_1'),
            MultiplexorTable(multiplexorKey: 'Multiplexor_2'),
          ],
        ),
      ),
    );
  }
}