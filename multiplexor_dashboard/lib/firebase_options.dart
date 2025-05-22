// lib/firebase_options.dart

import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    throw UnsupportedError(
      'DefaultFirebaseOptions are not supported for this platform.',
    );
  }

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: "AIzaSyCGxa5c5a9DBm_BWOI7aF5RL90cX5d7fj0",
    authDomain: "realtime-t2.firebaseapp.com",
    databaseURL: "https://realtime-t2-default-rtdb.firebaseio.com",
    projectId: "realtime-t2",
    storageBucket: "realtime-t2.firebasestorage.app",
    messagingSenderId: "421559045982",
    appId: "1:421559045982:web:928893516007685020c9cf"
  );
}
