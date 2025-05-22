import 'package:flutter/material.dart';
import 'package:firebase_database/firebase_database.dart';

class VistaGeneralTab extends StatelessWidget {
  const VistaGeneralTab({super.key});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<DatabaseEvent>(
      stream: FirebaseDatabase.instance.ref('Multiplexor_1').onValue,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (!snapshot.hasData || snapshot.data!.snapshot.value == null) {
          return const Center(child: Text('No hay datos disponibles'));
        }

        final data = Map<String, dynamic>.from(snapshot.data!.snapshot.value as Map);
        final latestKey = data.keys.toList()..sort();
        final latestData = Map<String, dynamic>.from(data[latestKey.last]);

        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                child: Image.asset(
                    'assets/edificio.png',
                    width: double.infinity,
                    height: 350,
                    fit: BoxFit.contain,
                ),
                ),
              const SizedBox(height: 20),
              Wrap(
                spacing: 20,
                runSpacing: 10,
                alignment: WrapAlignment.center,
                children: latestData.entries.take(8).map((entry) {
                  return Chip(
                    label: Text('${entry.key}: ${entry.value}'),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  );
                }).toList(),
              ),
            ],
          ),
        );
      },
    );
  }
}
