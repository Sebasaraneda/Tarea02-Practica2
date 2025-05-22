import 'package:flutter/material.dart';
import 'package:firebase_database/firebase_database.dart';

class MultiplexorTable extends StatelessWidget {
  final String multiplexorKey; // Ej: "Multiplexor_1"

  const MultiplexorTable({required this.multiplexorKey, super.key});

  @override
  Widget build(BuildContext context) {
    final DatabaseReference _ref = FirebaseDatabase.instance.ref(multiplexorKey);

    return StreamBuilder<DatabaseEvent>(
      stream: _ref.onValue,
      builder: (context, snapshot) {
        if (snapshot.hasData && snapshot.data!.snapshot.value != null) {
          final data = Map<String, dynamic>.from(snapshot.data!.snapshot.value as Map);

          // Obtener la entrada más reciente
          final latestTimestamp = data.keys.toList().last;
          final sensors = Map<String, dynamic>.from(data[latestTimestamp]);

          final rows = sensors.entries.map((entry) {
            return DataRow(cells: [
              DataCell(Text(entry.key)),                        // Sensor_1
              DataCell(Text('${entry.value}')),                // 17.90
              DataCell(Text(latestTimestamp)),                 // Fecha y hora
            ]);
          }).toList();

          return LayoutBuilder(
            builder: (context, constraints) {
                return SingleChildScrollView(
                scrollDirection: Axis.vertical,
                child: ConstrainedBox(
                    constraints: BoxConstraints(minWidth: constraints.maxWidth),
                    child: DataTable(
                    columnSpacing: 24.0,
                    columns: const [
                        DataColumn(label: Expanded(child: Text('Sensor', style: TextStyle(fontWeight: FontWeight.bold)))),
                        DataColumn(label: Expanded(child: Text('Valor', style: TextStyle(fontWeight: FontWeight.bold)))),
                        DataColumn(label: Expanded(child: Text('Fecha y hora', style: TextStyle(fontWeight: FontWeight.bold)))),
                    ],
                    rows: rows,
                    ),
                ),
                );
            },
            );

        } else if (snapshot.hasError) {
          return Center(child: Text('Error al cargar datos'));
        } else {
          return Center(child: CircularProgressIndicator());
        }
      },
    );
  }
}
