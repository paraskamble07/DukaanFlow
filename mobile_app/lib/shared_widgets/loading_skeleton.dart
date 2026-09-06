import 'package:flutter/material.dart';
import '../core/constants/app_colors.dart';

class LoadingSkeleton extends StatelessWidget {
  final double height;
  final double width;
  final double borderRadius;

  const LoadingSkeleton({
    super.key,
    this.height = 20,
    this.width = double.infinity,
    this.borderRadius = 8,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      width: width,
      decoration: BoxDecoration(
        color: AppColors.borderLight.withOpacity(0.6),
        borderRadius: BorderRadius.circular(borderRadius),
      ),
    );
  }
}
